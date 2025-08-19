#!/usr/bin/env python3
"""
Test script to see the actual results from Gemini enricher
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
    gemini_api_key: str = os.getenv('GEMINI_API_KEY')

def test_norwegian_bank():
    """Test the Gemini enricher with the Norwegian bank from your database"""
    from src.equity_pipeline.enrichers.llm_investor_information import LLMInvestorInformationEnricher
    
    # Create test config
    config = TestConfig()
    
    # Create enricher
    enricher = LLMInvestorInformationEnricher(config)
    
    # Test with the Norwegian bank that was processed
    test_company = {
        'Ticker': 'RING NO Equity',
        'Security': 'SpareBank 1 Ringerike Hadeland'
    }
    
    try:
        logger.info("Testing Gemini LLM enricher with SpareBank 1 Ringerike Hadeland...")
        enriched_data = enricher.enrich(test_company)
        
        if enriched_data:
            print("\n" + "="*60)
            print("🏦 GEMINI LLM RESULTS FOR SPAREBANK 1 RINGERIKE HADELAND")
            print("="*60)
            
            # Print results in a nice format
            for key, value in enriched_data.items():
                if isinstance(value, list) and value:
                    print(f"\n📋 {key.upper()}:")
                    for i, item in enumerate(value, 1):
                        print(f"   {i}. {item}")
                elif isinstance(value, list) and not value:
                    print(f"\n📋 {key.upper()}: No items found")
                else:
                    print(f"\n🔗 {key.upper()}: {value}")
            
            print("\n" + "="*60)
            return True
        else:
            logger.warning("❌ No data returned from Gemini")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_norwegian_bank()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")