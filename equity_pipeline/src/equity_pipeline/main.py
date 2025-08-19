"""
Public Equities Data Pipeline with Supabase
A clean, modular pipeline for enriching company data with retry logic
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import Config
from .database import DatabaseManager
from .enrichers import (
    YahooFinanceEnricher,
    ISINEnricher,
    SectorClassificationEnricher,
    SECFilingsEnricher,
    LLMInvestorInformationEnricher
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enricher Registry - Enable/Disable Enrichers Here
# ============================================================================

ENABLED_ENRICHERS = [
    LLMInvestorInformationEnricher,  # Gemini LLM investor information enrichment
    # SECFilingsEnricher,  # Uncomment to enable SEC filings enrichment
    # YahooFinanceEnricher,  # Uncomment to enable Yahoo Finance enrichment
    # ISINEnricher,  # Uncomment to enable ISIN enrichment
    # SectorClassificationEnricher,  # Uncomment to enable BICS classification
]


# ============================================================================
# Pipeline Orchestrator
# ============================================================================

class EnrichmentPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db = DatabaseManager(config)
        self.enrichers = self._initialize_enrichers()
        self.results_buffer = []
        self.processed_count = 0
    
    def _initialize_enrichers(self) -> List[Any]:
        """Initialize enabled enricher instances"""
        enrichers = []
        for enricher_class in ENABLED_ENRICHERS:
            enrichers.append(enricher_class(self.config))
            logger.info(f"Enabled enricher: {enricher_class.__name__}")
        return enrichers
    
    def run(self, limit: Optional[int] = None) -> None:
        """Run the complete enrichment pipeline"""
        logger.info("Starting enrichment pipeline")
        start_time = datetime.now()
        
        # Fetch companies
        companies = self.db.fetch_companies(limit)
        total_companies = len(companies)

        logger.info(f"Total companies: {total_companies}")
        
        for idx, company in enumerate(companies):
            ticker = company.get('Ticker', 'Unknown')
            logger.info(f"Processing {ticker} ({idx + 1}/{total_companies})")
            
            try:
                # Run all enrichers
                enriched_data = self._enrich_company(company)
                
                if enriched_data:
                    enriched_data['Ticker'] = ticker
                    enriched_data['last_enriched'] = datetime.now().isoformat()
                    self.results_buffer.append(enriched_data)
                
                # Save periodically
                if len(self.results_buffer) >= self.config.save_frequency:
                    self._save_buffer()
                
                self.processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process {ticker}: {e}")
                self._log_enrichment_error(ticker, str(e))
        
        # Save any remaining results
        if self.results_buffer:
            self._save_buffer()
        
        # Log summary
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Pipeline completed: {self.processed_count}/{total_companies} companies in {duration:.2f}s")
    
    def _enrich_company(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Run all enrichers for a single company"""
        enriched_data = {}
        
        for enricher in self.enrichers:
            try:
                result = enricher.enrich(company)
                enriched_data.update(result)
            except Exception as e:
                logger.warning(f"{enricher.name} failed for {company.get('Ticker')}: {e}")
        
        return enriched_data
    
    def _save_buffer(self) -> None:
        """Save buffered results to database"""
        if not self.results_buffer:
            return
        
        logger.info(f"Saving {len(self.results_buffer)} enriched records to database")
        
        try:
            self.db.batch_update_companies(self.results_buffer)
            self.results_buffer.clear()
        except Exception as e:
            logger.error(f"Failed to save buffer: {e}")
    
    def _log_enrichment_error(self, ticker: str, error: str) -> None:
        """Log enrichment errors for debugging"""
        log_entry = {
            'ticker': ticker,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'enricher': 'pipeline'
        }
        self.db.create_enrichment_log(log_entry)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the pipeline"""
    try:
        # Initialize configuration
        config = Config()
        
        # Create and run pipeline
        pipeline = EnrichmentPipeline(config)
        
        # Run with optional limit for testing
        pipeline.run(limit=1)  # Test with 1 company
        # pipeline.run()  # Process all companies
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()