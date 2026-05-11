"""
Robust HTTP Client with Retry Logic and Rate Limiting
"""

import asyncio
import time
from typing import Optional, Dict, Any
from collections import deque

import httpx

from backend.config import config
from backend.exceptions import APIException, RateLimitException
from backend.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, period: int):
        """
        Args:
            max_requests: Maximum number of requests
            period: Time period in seconds
        """
        self.max_requests = max_requests
        self.period = period
        self.requests = deque()

    async def acquire(self):
        """Wait until a request can be made."""
        now = time.time()

        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - self.period:
            self.requests.popleft()

        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.period - now
            if sleep_time > 0:
                logger.debug(f"Rate limit reached. Waiting {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
                return await self.acquire()

        self.requests.append(now)


class HTTPClient:
    """HTTP client with retry logic, rate limiting, and error handling."""

    def __init__(
        self,
        timeout: int = None,
        max_retries: int = None,
        backoff_factor: float = None,
        rate_limit_requests: int = None,
        rate_limit_period: int = None,
    ):
        self.timeout = timeout or config.REQUEST_TIMEOUT
        self.max_retries = max_retries or config.MAX_RETRIES
        self.backoff_factor = backoff_factor or config.RETRY_BACKOFF_FACTOR

        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests or config.RATE_LIMIT_REQUESTS,
            period=rate_limit_period or config.RATE_LIMIT_PERIOD,
        )

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        api_name: str = "API",
        retry_on_status: Optional[list] = None,
    ) -> Dict[Any, Any]:
        """
        Make an HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            params: Query parameters
            json: JSON body
            api_name: Name of the API for logging
            retry_on_status: List of status codes to retry on

        Returns:
            Response JSON data

        Raises:
            APIException: On API errors
            RateLimitException: On rate limit errors
        """
        retry_on_status = retry_on_status or [429, 500, 502, 503, 504]
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json,
                    )

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", self.backoff_factor ** (attempt + 1)))
                        logger.warning(f"{api_name} rate limited. Retry after {retry_after}s")

                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise RateLimitException(api_name, retry_after)

                    # Handle server errors
                    if response.status_code in retry_on_status:
                        if attempt < self.max_retries - 1:
                            wait_time = self.backoff_factor ** attempt
                            logger.warning(
                                f"{api_name} returned {response.status_code}. "
                                f"Retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise APIException(
                                f"Request failed with status {response.status_code}",
                                api_name,
                                response.status_code
                            )

                    # Raise for other HTTP errors
                    response.raise_for_status()

                    # Success
                    try:
                        return response.json()
                    except Exception:
                        # If response is not JSON, return text
                        return {"data": response.text}

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(f"{api_name} HTTP error: {e.response.status_code} - {e}")
                raise APIException(
                    f"HTTP {e.response.status_code}: {e}",
                    api_name,
                    e.response.status_code
                )

            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"{api_name} request error: {e}. "
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"{api_name} request failed after {self.max_retries} attempts: {e}")
                    raise APIException(str(e), api_name)

            except Exception as e:
                logger.error(f"{api_name} unexpected error: {e}")
                raise APIException(str(e), api_name)

        raise APIException(f"Request failed after {self.max_retries} attempts: {last_exception}", api_name)

    async def get(self, url: str, **kwargs) -> Dict:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)


# Global HTTP client instances
newsdata_client = HTTPClient()
ai_client = HTTPClient(timeout=config.AI_TIMEOUT)
market_client = HTTPClient()
