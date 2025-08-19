"""
LLM-powered investor information enricher using Google Gemini.
"""

import json
import logging
from typing import Dict, Any, Optional

from google import genai

from .base import BaseEnricher, retry_on_failure

logger = logging.getLogger(__name__)


class LLMInvestorInformationEnricher(BaseEnricher):
    """Enriches companies with investor information using Gemini LLM"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model = "gemini-2.5-flash"
        
        # Prompt template for investor information extraction
        self.prompt_template = """
You are an information research and extractor agent for public equities. You will be given a company, find the following information:

Primary Website URL: primary website
Investor Section URL: found on primary website  
Latest Corporate Presentation URLs: [list of working URLs of latest presentations listed in the investor section, could be more than one]

Company: {company_name} (Ticker: {ticker})

Answer in the following JSON format:
{{
    "primary_website": "https://...",
    "investor_section_url": "https://...",
    "corporate_presentation_urls": [
        "https://...",
        "https://..."
    ]
}}

Only return valid, working URLs. If you cannot find certain information, use null for that field.
"""
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch investor information using Gemini LLM"""
        if not self.validate_input(company):
            return {}
        
        ticker = company['Ticker']
        company_name = company.get('Security', ticker)
        
        logger.info(f"Fetching investor information for {company_name} ({ticker}) using Gemini LLM")
        
        try:
            # Create the prompt
            prompt = self.prompt_template.format(
                company_name=company_name,
                ticker=ticker
            )
            
            # Generate content using Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            # Parse the response
            investor_data = self._parse_llm_response(response.text)
            
            if investor_data:
                # Add metadata
                enriched_data = {
                    'llm_primary_website': investor_data.get('primary_website'),
                    'llm_investor_section_url': investor_data.get('investor_section_url'),
                    'llm_corporate_presentations': investor_data.get('corporate_presentation_urls'),
                    'llm_presentations_count': len(investor_data.get('corporate_presentation_urls', [])),
                    'llm_enrichment_model': self.model,
                    'llm_last_updated': self._get_current_timestamp(),
                }
                
                # Clean None values
                enriched_data = {k: v for k, v in enriched_data.items() if v is not None}
                
                logger.info(f"Successfully extracted investor information for {ticker}")
                return enriched_data
            else:
                logger.warning(f"Could not extract valid investor information for {ticker}")
                return {}
                
        except Exception as e:
            logger.error(f"LLM investor information enrichment failed for {ticker}: {e}")
            raise
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response and extract structured data"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate required fields
            if isinstance(data, dict):
                return data
            else:
                logger.warning(f"LLM response is not a valid dictionary: {data}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()