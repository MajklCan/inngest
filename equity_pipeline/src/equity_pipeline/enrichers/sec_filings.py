"""
SEC filings enricher for equity data pipeline.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

import pandas as pd
from edgar import Company, set_identity

from .base import BaseEnricher, retry_on_failure
from ..database import DatabaseManager

logger = logging.getLogger(__name__)


class SECFilingsEnricher(BaseEnricher):
    """Enriches companies with SEC filing links and metadata"""
    
    # Important filing types to track
    FILING_TYPES = {
        '10-K': 'Annual report',
        '10-Q': 'Quarterly report',
        '8-K': 'Current report (material events)',
        'DEF 14A': 'Proxy statement',
        '20-F': 'Annual report (foreign)',
        'S-1': 'Registration statement',
        '424B': 'Prospectus',
        '11-K': 'Employee stock plan annual report',
        'SC 13D': 'Beneficial ownership report',
        'SC 13G': 'Beneficial ownership report (passive)',
        '13F': 'Institutional holdings',
        'DEFA14A': 'Additional proxy materials',
        'S-3': 'Registration statement (simplified)',
        'S-8': 'Employee benefit plan registration',
        '6-K': 'Current report (foreign)',
        '40-F': 'Annual report (Canadian)',
    }
    
    def __init__(self, config):
        super().__init__(config)
        self.lookback_date = datetime.now() - pd.Timedelta(days=config.filings_lookback_days)
        # Set SEC identity for API access from config
        set_identity(config.edgar_identity)
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch SEC filing links and metadata"""
        if not self.validate_input(company):
            return {}
        
        raw_ticker = company['Ticker']
        # Clean ticker: remove " Equity" suffix and exchange codes
        ticker = raw_ticker.split()[0] if raw_ticker else raw_ticker
        
        logger.info(f"Fetching SEC filings for {ticker} (from {raw_ticker})")
        
        try:
            # Get company from EDGAR
            edgar_company = Company(ticker)
            
            # Check if company was found in SEC database
            if edgar_company is None:
                logger.info(f"Company {ticker} not found in SEC EDGAR database (likely non-US company)")
                return {}
            
            # Get filings for the lookback period
            filings = edgar_company.get_filings(
                form=[form for form in self.FILING_TYPES.keys()]
            ).filter(date=f"{self.lookback_date.strftime('%Y-%m-%d')}:")
            
            # Process filings into structured data
            filings_data = self._process_filings(filings)
            
            # Create enriched data structure
            enriched_data = {
                'sec_cik': edgar_company.cik,
                'sec_company_name': edgar_company.name,
                'sec_filings_count': len(filings_data),
                'sec_latest_10k': self._get_latest_filing_url(filings_data, '10-K'),
                'sec_latest_10q': self._get_latest_filing_url(filings_data, '10-Q'),
                'sec_latest_8k': self._get_latest_filing_url(filings_data, '8-K'),
                'sec_latest_proxy': self._get_latest_filing_url(filings_data, 'DEF 14A'),
                'sec_filings_summary': self._create_filings_summary(filings_data),
                'sec_last_updated': datetime.now().isoformat(),
            }
            
            # Store detailed filings in a separate table (if needed)
            self._store_detailed_filings(ticker, filings_data)
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"SEC filings enrichment failed for {ticker}: {e}")
            raise
    
    def _process_filings(self, filings) -> List[Dict[str, Any]]:
        """Process raw filings into structured data"""
        processed_filings = []
        
        for filing in filings:
            try:
                filing_data = {
                    'form_type': filing.form,
                    'filing_date': filing.filing_date.isoformat() if filing.filing_date else None,
                    'accession_number': filing.accession_number,
                    'description': self.FILING_TYPES.get(filing.form, filing.form),
                    'filing_url': filing.url,
                    'document_url': filing.document.url if filing.document else None,
                    'interactive_url': filing.viewer_url if hasattr(filing, 'viewer_url') else None,
                    'file_number': filing.file_number if hasattr(filing, 'file_number') else None,
                    'size': filing.size if hasattr(filing, 'size') else None,
                }
                
                # Get primary document link
                if hasattr(filing, 'attachments'):
                    primary_doc = next((att for att in filing.attachments 
                                       if att.document_type == filing.form), None)
                    if primary_doc:
                        filing_data['primary_document_url'] = primary_doc.url
                
                processed_filings.append(filing_data)
                
            except Exception as e:
                logger.warning(f"Failed to process filing: {e}")
                continue
        
        # Sort by date (most recent first)
        processed_filings.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
        
        return processed_filings
    
    def _get_latest_filing_url(self, filings: List[Dict], form_type: str) -> Optional[str]:
        """Get the URL of the most recent filing of a specific type"""
        for filing in filings:
            if filing.get('form_type') == form_type:
                return filing.get('document_url') or filing.get('filing_url')
        return None
    
    def _create_filings_summary(self, filings: List[Dict]) -> Dict[str, Any]:
        """Create a summary of all filings by type"""
        summary = defaultdict(lambda: {'count': 0, 'latest_date': None})
        
        for filing in filings:
            form_type = filing.get('form_type')
            if form_type:
                summary[form_type]['count'] += 1
                if not summary[form_type]['latest_date'] or \
                   filing.get('filing_date', '') > summary[form_type]['latest_date']:
                    summary[form_type]['latest_date'] = filing.get('filing_date')
        
        return dict(summary)
    
    def _store_detailed_filings(self, ticker: str, filings: List[Dict]) -> None:
        """Store detailed filings in a separate table for reference"""
        try:
            # You might want to create a separate table for this
            # CREATE TABLE company_filings (
            #     id SERIAL PRIMARY KEY,
            #     ticker TEXT,
            #     form_type TEXT,
            #     filing_date DATE,
            #     accession_number TEXT,
            #     filing_url TEXT,
            #     document_url TEXT,
            #     metadata JSONB,
            #     created_at TIMESTAMP DEFAULT NOW()
            # );
            
            db = DatabaseManager(self.config)
            
            for filing in filings[:20]:  # Store only recent 20 filings to avoid bloat
                filing_record = {
                    'ticker': ticker,
                    'form_type': filing.get('form_type'),
                    'filing_date': filing.get('filing_date'),
                    'accession_number': filing.get('accession_number'),
                    'filing_url': filing.get('filing_url'),
                    'document_url': filing.get('document_url'),
                    'metadata': filing,  # Store full data as JSONB
                }
                
                try:
                    db.client.table('company_filings').upsert(
                        filing_record,
                        on_conflict='ticker,accession_number'
                    ).execute()
                except:
                    # Table might not exist, skip for now
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to store detailed filings for {ticker}: {e}")