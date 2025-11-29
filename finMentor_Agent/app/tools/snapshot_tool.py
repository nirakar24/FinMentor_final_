"""
Tool for fetching user financial snapshot from external API.
"""
from typing import Dict, Any
import httpx
from app.config import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


async def fetch_snapshot(user_id: str) -> Dict[str, Any]:
    """
    Fetch user financial snapshot from the Snapshot API.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Dictionary containing user financial snapshot data
        
    Raises:
        RuntimeError: If API call fails
    """
    url = f"{settings.api_base_url}/snapshot/{user_id}"
    
    try:
        logger.info(f"Fetching snapshot for user: {user_id} from {url}")
        
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        logger.info(f"Successfully fetched snapshot for user: {user_id}")
        logger.debug(f"Snapshot data: {data}")
        return data
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching snapshot: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Failed to fetch snapshot: HTTP {e.response.status_code}")
    
    except httpx.RequestError as e:
        logger.error(f"Network error fetching snapshot: {e}")
        raise RuntimeError(f"Network error fetching snapshot: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error fetching snapshot: {e}")
        raise RuntimeError(f"Unexpected error: {str(e)}")
