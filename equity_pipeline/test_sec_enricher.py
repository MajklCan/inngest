#!/usr/bin/env python3
"""
Test script for SEC filings enricher without database connection
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration that doesn't require Supabase"""
    filings_lookback_days: int = 365
    edgar_identity: str = os.getenv('EDGAR_IDENTITY', 'Test Pipeline test@example.com')

def test_sec_enricher():
    """Test the SEC enricher with a sample ticker"""
    from src.equity_pipeline.enrichers.sec_filings import SECFilingsEnricher
    
    # Create test config
    config = TestConfig()
    
    # Create enricher
    enricher = SECFilingsEnricher(config)
    
    # Test with a sample company
    test_company = {'Ticker': 'AAPL'}
    
    try:
        logger.info("Testing SEC enricher with AAPL...")
        enriched_data = enricher.enrich(test_company)
        
        logger.info("SEC enrichment successful!")
        logger.info(f"Enriched data keys: {list(enriched_data.keys())}")
        
        # Print results
        for key, value in enriched_data.items():
            if isinstance(value, dict):
                logger.info(f"{key}: {value}")
            else:
                logger.info(f"{key}: {value}")
                
        return True
        
    except Exception as e:
        logger.error(f"SEC enrichment failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sec_enricher()
    if success:
        print("\n✅ SEC Enricher test completed successfully!")
    else:
        print("\n❌ SEC Enricher test failed!")