"""
Tool for generating financial advice using external Advice Generator API.
"""
from typing import Dict, Any
import httpx
from app.config import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


async def generate_advice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized financial advice based on user data and analysis.
    
    Args:
        payload: Request payload containing user_id, rules, behavior, persona
    
    Returns:
        Dictionary containing generated financial advice
        
    Raises:
        RuntimeError: If API call fails
    """
    url = f"{settings.api_base_url}/advice/generate"
    
    try:
        logger.info(f"Generating financial advice at {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        
        logger.info("Advice generation completed successfully")
        logger.debug(f"Advice result: {data}")
        return data
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error generating advice: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Failed to generate advice: HTTP {e.response.status_code}")
    
    except httpx.RequestError as e:
        logger.error(f"Network error generating advice: {e}")
        raise RuntimeError(f"Network error generating advice: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error generating advice: {e}")
        raise RuntimeError(f"Unexpected error: {str(e)}")
