"""
Base enricher class and utilities for the equity pipeline.
"""

import logging
import time
from typing import Dict, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 2, delay: float = 1.0):
    """Decorator to retry failed operations"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator


class BaseEnricher:
    """Base class for all data enrichers"""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method in subclasses"""
        raise NotImplementedError
    
    def validate_input(self, company: Dict[str, Any]) -> bool:
        """Validate if company data is suitable for enrichment"""
        return 'Ticker' in company and company['Ticker']