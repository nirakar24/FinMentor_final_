"""
HTTP client for making async API calls to external services.
"""
import httpx
from typing import Any, Dict, Optional
from app.config import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


class HTTPClient:
    """Async HTTP client for external API calls."""
    
    def __init__(
        self,
        timeout: int = settings.api_timeout,
        max_retries: int = settings.api_max_retries
    ):
        """
        Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an async GET request.
        
        Args:
            url: Target URL
            params: Query parameters
            headers: Request headers
        
        Returns:
            Response JSON data
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"GET request to {url}")
            
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"Response from {url}: {data}")
                return data
            
            except httpx.HTTPError as e:
                logger.error(f"HTTP error occurred: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
    
    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an async POST request.
        
        Args:
            url: Target URL
            json: JSON payload
            data: Form data payload
            headers: Request headers
        
        Returns:
            Response JSON data
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"POST request to {url}")
            
            try:
                response = await client.post(
                    url,
                    json=json,
                    data=data,
                    headers=headers
                )
                response.raise_for_status()
                response_data = response.json()
                
                logger.debug(f"Response from {url}: {response_data}")
                return response_data
            
            except httpx.HTTPError as e:
                logger.error(f"HTTP error occurred: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise


# Global HTTP client instance
http_client = HTTPClient()
