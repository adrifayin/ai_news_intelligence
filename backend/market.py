"""
Market Data Integration — Alpha Vantage (stocks) + Polymarket (predictions).
"""

import os
import time
from typing import Optional

import httpx


ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"

POLYMARKET_BASE = "https://gamma-api.polymarket.com"


# ═══════════════════════════════════════════
# Simple In-Memory Cache
# ═══════════════════════════════════════════

class SimpleCache:
    """TTL-based in-memory cache to reduce API calls."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key: str):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value):
        self._cache[key] = (value, time.time())


_stock_cache = SimpleCache(ttl_seconds=300)   # 5 min cache
_market_cache = SimpleCache(ttl_seconds=120)  # 2 min cache


# ═══════════════════════════════════════════
# Alpha Vantage — Stock Data
# ═══════════════════════════════════════════

async def get_stock_quote(ticker: str) -> Optional[dict]:
    """
    Get real-time stock quote from Alpha Vantage.
    Free tier: 25 requests/day, so we cache aggressively.
    """
    if not ALPHA_VANTAGE_KEY:
        return _get_mock_stock(ticker)

    cache_key = f"quote_{ticker}"
    cached = _stock_cache.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(ALPHA_VANTAGE_BASE, params={
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_KEY,
            })
            response.raise_for_status()
            data = response.json()

            quote = data.get("Global Quote", {})
            if not quote:
                return _get_mock_stock(ticker)

            result = {
                "ticker": ticker,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                "volume": int(quote.get("06. volume", 0)),
                "latest_trading_day": quote.get("07. latest trading day", ""),
                "previous_close": float(quote.get("08. previous close", 0)),
            }

            _stock_cache.set(cache_key, result)
            return result

    except Exception as e:
        print(f"Alpha Vantage error for {ticker}: {e}")
        return _get_mock_stock(ticker)


def _get_mock_stock(ticker: str) -> dict:
    """Return reasonable mock data when API is unavailable."""
    import random
    base_prices = {
        "AAPL": 198.5, "GOOGL": 177.2, "MSFT": 428.3, "AMZN": 186.7,
        "TSLA": 245.8, "META": 505.6, "NVDA": 875.3, "JPM": 198.4,
        "V": 279.6, "WMT": 168.9, "JNJ": 155.3, "XOM": 108.7,
    }
    base = base_prices.get(ticker, 100 + random.random() * 200)
    change = round((random.random() - 0.5) * 10, 2)
    return {
        "ticker": ticker,
        "price": round(base + change, 2),
        "change": change,
        "change_percent": str(round(change / base * 100, 2)),
        "volume": random.randint(1000000, 50000000),
        "latest_trading_day": "",
        "previous_close": round(base, 2),
    }


# ═══════════════════════════════════════════
# Polymarket — Prediction Markets
# ═══════════════════════════════════════════

async def get_prediction_markets(limit: int = 20, offset: int = 0) -> list:
    """
    Fetch active prediction markets from Polymarket Gamma API.
    Public API — no authentication required.
    """
    cache_key = f"markets_{limit}_{offset}"
    cached = _market_cache.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{POLYMARKET_BASE}/markets", params={
                "limit": limit,
                "offset": offset,
                "closed": "false",
                "order": "volume",
                "ascending": "false",
            })
            response.raise_for_status()
            markets_data = response.json()

            markets = []
            for m in markets_data:
                # Parse outcome prices
                outcomes = []
                outcome_prices_str = m.get("outcomePrices", "[]")
                outcomes_str = m.get("outcomes", "[]")

                try:
                    import json
                    prices = json.loads(outcome_prices_str) if isinstance(outcome_prices_str, str) else outcome_prices_str
                    names = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                except (json.JSONDecodeError, TypeError):
                    prices = []
                    names = []

                for i, name in enumerate(names):
                    price = float(prices[i]) if i < len(prices) else 0.5
                    outcomes.append({
                        "name": name,
                        "price": round(price, 4),
                        "percent": round(price * 100, 1),
                    })

                market = {
                    "id": m.get("id", ""),
                    "question": m.get("question", ""),
                    "description": (m.get("description", "") or "")[:300],
                    "category": _categorize_market(m.get("question", "")),
                    "outcomes": outcomes,
                    "volume": float(m.get("volume", 0) or 0),
                    "liquidity": float(m.get("liquidity", 0) or 0),
                    "end_date": m.get("endDate", ""),
                    "image": m.get("image", ""),
                    "active": m.get("active", True),
                }
                markets.append(market)

            _market_cache.set(cache_key, markets)
            return markets

    except Exception as e:
        print(f"Polymarket API error: {e}")
        return _get_mock_markets()


def _categorize_market(question: str) -> str:
    """Simple keyword-based categorization of prediction markets."""
    q = question.lower()
    if any(w in q for w in ["election", "president", "congress", "vote", "political", "trump", "biden"]):
        return "Politics"
    if any(w in q for w in ["stock", "bitcoin", "crypto", "gdp", "inflation", "fed", "economy", "market"]):
        return "Economics"
    if any(w in q for w in ["ai", "tech", "apple", "google", "microsoft", "software", "launch"]):
        return "Technology"
    if any(w in q for w in ["climate", "space", "nasa", "research", "study", "discovery"]):
        return "Science"
    if any(w in q for w in ["war", "conflict", "military", "peace", "treaty"]):
        return "Geopolitics"
    return "Other"


def _get_mock_markets() -> list:
    """Fallback mock prediction markets."""
    return [
        {
            "id": "mock-1",
            "question": "Will AI surpass human-level reasoning by 2027?",
            "description": "Resolution based on consensus benchmarks.",
            "category": "Technology",
            "outcomes": [
                {"name": "Yes", "price": 0.32, "percent": 32.0},
                {"name": "No", "price": 0.68, "percent": 68.0},
            ],
            "volume": 1250000,
            "liquidity": 450000,
            "end_date": "2027-12-31",
            "image": "",
            "active": True,
        },
        {
            "id": "mock-2",
            "question": "Will Bitcoin exceed $150,000 in 2026?",
            "description": "Based on market price at any point in 2026.",
            "category": "Economics",
            "outcomes": [
                {"name": "Yes", "price": 0.45, "percent": 45.0},
                {"name": "No", "price": 0.55, "percent": 55.0},
            ],
            "volume": 3400000,
            "liquidity": 890000,
            "end_date": "2026-12-31",
            "image": "",
            "active": True,
        },
        {
            "id": "mock-3",
            "question": "Will global temperatures set a new record in 2026?",
            "description": "Based on NASA GISS data.",
            "category": "Science",
            "outcomes": [
                {"name": "Yes", "price": 0.72, "percent": 72.0},
                {"name": "No", "price": 0.28, "percent": 28.0},
            ],
            "volume": 560000,
            "liquidity": 120000,
            "end_date": "2027-01-31",
            "image": "",
            "active": True,
        },
    ]


async def get_market_events(limit: int = 10) -> list:
    """Fetch market events from Polymarket."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{POLYMARKET_BASE}/events", params={
                "limit": limit,
                "closed": "false",
                "order": "volume",
                "ascending": "false",
            })
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Polymarket events error: {e}")
        return []


# ═══════════════════════════════════════════
# Sector Heatmap Data
# ═══════════════════════════════════════════

SECTOR_TICKERS = {
    "Technology": ["AAPL", "GOOGL", "MSFT", "NVDA", "META"],
    "Finance": ["JPM", "GS", "BAC", "V", "MA"],
    "Energy": ["XOM", "CVX", "COP", "SLB"],
    "Healthcare": ["JNJ", "PFE", "UNH", "ABBV"],
    "Consumer": ["AMZN", "WMT", "NKE", "SBUX"],
}


async def get_sector_heatmap(ticker_sentiments: list) -> dict:
    """
    Build sector heatmap from ticker sentiment data.
    Maps tickers to sectors and averages sentiment.
    """
    # Build ticker -> sentiment map
    ticker_map = {t["ticker"]: t["avg_sentiment"] for t in ticker_sentiments}

    heatmap = {}
    for sector, tickers in SECTOR_TICKERS.items():
        sentiments = [ticker_map[t] for t in tickers if t in ticker_map]
        if sentiments:
            heatmap[sector] = round(sum(sentiments) / len(sentiments), 3)
        else:
            heatmap[sector] = 0.0

    return heatmap


# ═══════════════════════════════════════════
# Weather Integration — OpenWeatherMap
# ═══════════════════════════════════════════

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
_weather_cache = SimpleCache(ttl_seconds=1800)  # 30 min cache

# Market-relevant weather hubs
WEATHER_HUBS = {
    "Houston": {"sector": "Energy", "impact": "Oil/gas production & refining operations"},
    "Chicago": {"sector": "Agriculture", "impact": "Grain, soybean & livestock futures"},
    "New York": {"sector": "Finance", "impact": "Major financial markets & trading"},
    "San Francisco": {"sector": "Technology", "impact": "Tech sector & VC activity"},
    "London": {"sector": "Global Finance", "impact": "FTSE, commodities & forex"},
}


async def get_weather(city: str) -> dict:
    """
    Get current weather for a city from OpenWeatherMap.
    Returns structured weather data with market impact context.
    """
    cache_key = f"weather_{city.lower()}"
    cached = _weather_cache.get(cache_key)
    if cached:
        return cached

    if not OPENWEATHER_API_KEY:
        return _get_mock_weather(city)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                }
            )
            response.raise_for_status()
            data = response.json()

            hub = WEATHER_HUBS.get(city, {})
            result = {
                "city": city,
                "temp": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "description": data["weather"][0]["description"].title(),
                "icon": data["weather"][0]["icon"],
                "humidity": data["main"]["humidity"],
                "wind_speed": round(data["wind"]["speed"], 1),
                "sector": hub.get("sector", "General"),
                "market_impact": hub.get("impact", ""),
            }

            _weather_cache.set(cache_key, result)
            return result

    except Exception as e:
        print(f"OpenWeatherMap error for {city}: {e}")
        return _get_mock_weather(city)


def _get_mock_weather(city: str) -> dict:
    """Fallback mock weather data."""
    import random
    hub = WEATHER_HUBS.get(city, {})
    conditions = ["Clear Sky", "Partly Cloudy", "Light Rain", "Overcast", "Sunny"]
    return {
        "city": city,
        "temp": round(random.uniform(10, 35), 1),
        "feels_like": round(random.uniform(8, 37), 1),
        "description": random.choice(conditions),
        "icon": "02d",
        "humidity": random.randint(30, 85),
        "wind_speed": round(random.uniform(1, 15), 1),
        "sector": hub.get("sector", "General"),
        "market_impact": hub.get("impact", ""),
    }


async def get_weather_hub() -> list:
    """Get weather for all market-relevant cities."""
    results = []
    for city in WEATHER_HUBS:
        weather = await get_weather(city)
        results.append(weather)
    return results
