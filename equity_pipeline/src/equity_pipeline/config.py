"""
Configuration module for the equity pipeline.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Central configuration for the pipeline"""
    supabase_url: str = field(default_factory=lambda: os.getenv('SUPABASE_URL'))
    supabase_key: str = field(default_factory=lambda: os.getenv('SUPABASE_KEY'))
    batch_size: int = 10
    save_frequency: int = 5  # Save every N companies
    max_retries: int = 2
    retry_delay: float = 1.0
    
    # SEC Filings configuration
    filings_lookback_days: int = field(default_factory=lambda: int(os.getenv('FILINGS_LOOKBACK_DAYS', '365')))
    edgar_identity: str = field(default_factory=lambda: os.getenv('EDGAR_IDENTITY', 'Your Company Name your.email@company.com'))
    
    # Gemini LLM configuration
    gemini_api_key: str = field(default_factory=lambda: os.getenv('GEMINI_API_KEY'))
    
    def __post_init__(self):
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials in environment variables")