"""
Database operations module for the equity pipeline.
"""

import logging
from typing import Dict, List, Any, Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles all Supabase database operations"""
    
    def __init__(self, config):
        self.config = config
        self.client: Client = create_client(config.supabase_url, config.supabase_key)
        logger.info("Connected to Supabase")
    
    def fetch_companies(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch companies from the database"""
        query = self.client.table('companies_bbt').select('*')
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        logger.info(f"Fetched {len(response.data)} companies")
        return response.data
    
    def update_company(self, ticker: str, updates: Dict[str, Any]) -> None:
        """Update a single company record"""
        try:
            self.client.table('companies_bbt').update(updates).eq('Ticker', ticker).execute()
            logger.debug(f"Updated {ticker} with {len(updates)} fields")
        except Exception as e:
            logger.error(f"Failed to update {ticker}: {e}")
            raise
    
    def batch_update_companies(self, updates: List[Dict[str, Any]]) -> None:
        """Batch update multiple companies"""
        for update in updates:
            if 'Ticker' in update:
                ticker = update['Ticker']
                self.update_company(ticker, update)
    
    def create_enrichment_log(self, log_entry: Dict[str, Any]) -> None:
        """Log enrichment activities to a separate table"""
        try:
            self.client.table('enrichment_logs').insert(log_entry).execute()
        except:
            # Table might not exist, create it
            logger.warning("Enrichment logs table might not exist")