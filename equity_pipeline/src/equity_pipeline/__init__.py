"""
Public Equities Data Pipeline with Supabase
A clean, modular pipeline for enriching company data with retry logic
"""

__version__ = "1.0.0"

from .main import EnrichmentPipeline, main
from .config import Config
from .database import DatabaseManager

__all__ = [
    'EnrichmentPipeline',
    'Config',
    'DatabaseManager',
    'main'
]