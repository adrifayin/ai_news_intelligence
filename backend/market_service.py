"""
Enhanced Market Data Service
Integrates Marketstack API for real-time stock data
"""

import os
import asyncio
import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for fetching real-time market data from Marketstack API."""

    def __init__(self):
        self.api_key = os.getenv("MARKETSTACK_API_KEY", "")
        self.base_url = "http://api.marketstack.com/v1"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest stock quote for a symbol."""
        if not self.available:
            logger.warning("Marketstack API key not configured")
            return None

        # Check cache
        cache_key = f"quote_{symbol}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_data

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/eod/latest",
                    params={
                        "access_key": self.api_key,
                        "symbols": symbol.upper(),
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data.get("data") and len(data["data"]) > 0:
                    quote = data["data"][0]
                    result = {
                        "symbol": quote["symbol"],
                        "price": quote["close"],
                        "open": quote["open"],
                        "high": quote["high"],
                        "low": quote["low"],
                        "volume": quote["volume"],
                        "change": quote["close"] - quote["open"],
                        "change_percent": ((quote["close"] - quote["open"]) / quote["open"] * 100) if quote["open"] else 0,
                        "date": quote["date"],
                    }

                    # Cache result
                    self.cache[cache_key] = (datetime.now(), result)
                    return result

                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"Marketstack HTTP error for {symbol}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Get quotes for multiple symbols (batch request)."""
        if not self.available:
            return {symbol: None for symbol in symbols}

        # Marketstack API limits: 100 symbols per request
        symbols_str = ",".join([s.upper() for s in symbols[:100]])

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{self.base_url}/eod/latest",
                    params={
                        "access_key": self.api_key,
                        "symbols": symbols_str,
                    }
                )
                response.raise_for_status()
                data = response.json()

                results = {}
                if data.get("data"):
                    for quote in data["data"]:
                        symbol = quote["symbol"]
                        results[symbol] = {
                            "symbol": symbol,
                            "price": quote["close"],
                            "open": quote["open"],
                            "high": quote["high"],
                            "low": quote["low"],
                            "volume": quote["volume"],
                            "change": quote["close"] - quote["open"],
                            "change_percent": ((quote["close"] - quote["open"]) / quote["open"] * 100) if quote["open"] else 0,
                            "date": quote["date"],
                        }

                # Fill in None for symbols not found
                for symbol in symbols:
                    if symbol.upper() not in results:
                        results[symbol.upper()] = None

                return results

        except Exception as e:
            logger.error(f"Error fetching multiple quotes: {e}")
            return {symbol: None for symbol in symbols}

    async def get_intraday_data(self, symbol: str, interval: str = "1hour") -> Optional[List[Dict]]:
        """Get intraday price data for a symbol."""
        if not self.available:
            return None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{self.base_url}/intraday",
                    params={
                        "access_key": self.api_key,
                        "symbols": symbol.upper(),
                        "interval": interval,
                        "limit": 24,  # Last 24 data points
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data.get("data"):
                    return [
                        {
                            "time": point["date"],
                            "price": point["close"],
                            "volume": point["volume"],
                        }
                        for point in data["data"]
                    ]

                return None

        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None

    async def get_market_movers(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Get top gainers and losers (requires premium plan)."""
        # This is a placeholder - would need premium Marketstack plan
        # For now, return empty
        return {"gainers": [], "losers": []}

    def clear_cache(self):
        """Clear the quote cache."""
        self.cache = {}


# Global instance
market_service = MarketDataService()
