"""
Yahoo Finance enricher for equity data pipeline.
"""

import logging
from typing import Dict, Any, Optional

import yfinance as yf

from .base import BaseEnricher, retry_on_failure

logger = logging.getLogger(__name__)


class YahooFinanceEnricher(BaseEnricher):
    """Enriches data using Yahoo Finance API"""
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and enrich data from Yahoo Finance"""
        if not self.validate_input(company):
            return {}
        
        ticker = company['Ticker']
        logger.info(f"Enriching {ticker} with Yahoo Finance data")
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant fields
            enriched_data = {
                'Market Cap': info.get('marketCap'),
                'EV': info.get('enterpriseValue'),
                'Avg D Val Traded 3M': self._calculate_avg_volume_value(stock),
                'GICS Sector': info.get('sector'),
                'GICS Ind Grp Name': info.get('industry'),
                'Cntry Tertry Of Dom': info.get('country'),
            }
            
            # Clean None values
            enriched_data = {k: v for k, v in enriched_data.items() if v is not None}
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Yahoo Finance enrichment failed for {ticker}: {e}")
            raise
    
    def _calculate_avg_volume_value(self, stock) -> Optional[float]:
        """Calculate 3-month average daily traded value"""
        try:
            hist = stock.history(period="3mo")
            if not hist.empty:
                avg_volume = hist['Volume'].mean()
                avg_price = hist['Close'].mean()
                return avg_volume * avg_price
        except:
            pass
        return None