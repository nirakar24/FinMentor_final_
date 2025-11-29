"""
Tool for detecting financial behavior patterns using external API.
"""
from typing import Dict, Any
import httpx
from app.config import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


async def detect_behavior(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect financial behavior patterns based on user data.
    
    Args:
        payload: Request payload containing behavior metrics
    
    Returns:
        Dictionary containing detected behavior patterns
        
    Raises:
        RuntimeError: If API call fails
    """
    url = f"{settings.api_base_url}/behavior/detect"
    
    try:
        logger.info(f"Detecting behavior patterns at {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        
        logger.info("Behavior detection completed successfully")
        logger.debug(f"Behavior detection result: {data}")
        return data
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error detecting behavior: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Failed to detect behavior: HTTP {e.response.status_code}")
    
    except httpx.RequestError as e:
        logger.error(f"Network error detecting behavior: {e}")
        raise RuntimeError(f"Network error detecting behavior: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error detecting behavior: {e}")
        raise RuntimeError(f"Unexpected error: {str(e)}")
