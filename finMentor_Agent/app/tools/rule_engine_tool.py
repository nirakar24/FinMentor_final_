"""
Tool for evaluating financial rules using external Rule Engine API.
"""
from typing import Dict, Any
import httpx
from app.config import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


async def evaluate_rules(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate financial rules based on user snapshot.
    
    Args:
        payload: Request payload containing user data and context
    
    Returns:
        Dictionary containing rule evaluation results
        
    Raises:
        RuntimeError: If API call fails
    """
    url = f"{settings.api_base_url}/evaluate"
    
    try:
        logger.info(f"Evaluating rules at {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        
        logger.info("Rule evaluation completed successfully")
        logger.debug(f"Rule evaluation result: {data}")
        return data
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error evaluating rules: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Failed to evaluate rules: HTTP {e.response.status_code}")
    
    except httpx.RequestError as e:
        logger.error(f"Network error evaluating rules: {e}")
        raise RuntimeError(f"Network error evaluating rules: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error evaluating rules: {e}")
        raise RuntimeError(f"Unexpected error: {str(e)}")
