#!/usr/bin/env python3
"""
Test script for Gemini LLM investor information enricher
"""

import logging
from dataclasses import dataclass
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
    """Test configuration for Gemini enricher"""
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', 'test_key')

def test_gemini_enricher():
    """Test the Gemini enricher with a sample ticker"""
    from src.equity_pipeline.enrichers.llm_investor_information import LLMInvestorInformationEnricher
    
    # Check if API key is available
    if not os.getenv('GEMINI_API_KEY'):
        logger.error("GEMINI_API_KEY not found in environment variables")
        logger.info("Please add your Gemini API key to .env file:")
        logger.info("GEMINI_API_KEY=your_api_key_here")
        return False
    
    # Create test config
    config = TestConfig()
    
    # Create enricher
    try:
        enricher = LLMInvestorInformationEnricher(config)
    except Exception as e:
        logger.error(f"Failed to create Gemini enricher: {e}")
        return False
    
    # Test with a sample company (Apple)
    test_company = {
        'Ticker': 'AAPL',
        'Security': 'Apple Inc'
    }
    
    try:
        logger.info("Testing Gemini LLM enricher with Apple Inc...")
        enriched_data = enricher.enrich(test_company)
        
        if enriched_data:
            logger.info("✅ Gemini LLM enrichment successful!")
            logger.info(f"Enriched data keys: {list(enriched_data.keys())}")
            
            # Print results
            for key, value in enriched_data.items():
                if isinstance(value, list):
                    logger.info(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:3]):  # Show first 3 items
                        logger.info(f"  - {item}")
                    if len(value) > 3:
                        logger.info(f"  ... and {len(value) - 3} more")
                else:
                    logger.info(f"{key}: {value}")
            
            return True
        else:
            logger.warning("❌ Gemini enrichment returned no data")
            return False
            
    except Exception as e:
        logger.error(f"Gemini enrichment failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_enricher()
    if success:
        print("\n🎉 Gemini LLM Enricher test completed successfully!")
        print("The enricher is ready to extract investor information using Gemini AI!")
    else:
        print("\n❌ Gemini LLM Enricher test failed!")
        print("Please check your GEMINI_API_KEY and try again.")