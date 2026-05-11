"""
Multi-Source News Fetcher
Fetches from NewsAPI, GNews, and The Guardian API
Rotates between sources for better coverage and rate limit management
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# API Configuration
# ═══════════════════════════════════════════

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GNEWS_KEY = os.getenv("GNEWS_API_KEY", "")
GUARDIAN_KEY = os.getenv("GUARDIAN_API_KEY", "")

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"
GNEWS_URL = "https://gnews.io/api/v4/top-headlines"
GUARDIAN_URL = "https://content.guardianapis.com/search"


# ═══════════════════════════════════════════
# NewsAPI Fetcher
# ═══════════════════════════════════════════

async def fetch_from_newsapi(category: str = "technology", page_size: int = 100) -> List[Dict]:
    """
    Fetch from NewsAPI.org
    Free tier: 100 requests/day, 100 articles per request
    """
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set, skipping NewsAPI")
        return []

    params = {
        "apiKey": NEWSAPI_KEY,
        "category": category,
        "language": "en",
        "pageSize": page_size
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(NEWSAPI_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles = data.get("articles", [])
                logger.info(f"✓ NewsAPI: fetched {len(articles)} articles ({category})")

                # Transform to our format
                normalized = []
                for article in articles:
                    normalized.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),  # Full content included
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                        "source_name": article.get("source", {}).get("name", "Unknown"),
                        "image_url": article.get("urlToImage"),
                        "category": category,
                        "source_api": "newsapi"
                    })

                return normalized
            else:
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.error("NewsAPI rate limit exceeded (429)")
        else:
            logger.error(f"NewsAPI HTTP error {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"NewsAPI fetch error: {e}")
        return []


# ═══════════════════════════════════════════
# GNews API Fetcher
# ═══════════════════════════════════════════

async def fetch_from_gnews(topic: str = "technology", max_articles: int = 10) -> List[Dict]:
    """
    Fetch from GNews.io
    Free tier: 100 requests/day, 10 articles per request
    Full article content included
    """
    if not GNEWS_KEY:
        logger.warning("GNEWS_API_KEY not set, skipping GNews")
        return []

    params = {
        "token": GNEWS_KEY,
        "topic": topic,
        "lang": "en",
        "max": max_articles
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GNEWS_URL, params=params)
            response.raise_for_status()
            data = response.json()

            articles = data.get("articles", [])
            logger.info(f"✓ GNews: fetched {len(articles)} articles ({topic})")

            # Transform to our format
            normalized = []
            for article in articles:
                normalized.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),  # Full content
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source_name": article.get("source", {}).get("name", "Unknown"),
                    "image_url": article.get("image"),
                    "category": topic,
                    "source_api": "gnews"
                })

            return normalized

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.error("GNews rate limit exceeded (429)")
        else:
            logger.error(f"GNews HTTP error {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"GNews fetch error: {e}")
        return []


# ═══════════════════════════════════════════
# The Guardian API Fetcher
# ═══════════════════════════════════════════

async def fetch_from_guardian(section: str = "technology", page_size: int = 50) -> List[Dict]:
    """
    Fetch from The Guardian API
    Free tier: 12 requests/second, 5000/day
    Very high quality articles with full body text
    """
    if not GUARDIAN_KEY:
        logger.warning("GUARDIAN_API_KEY not set, skipping Guardian")
        return []

    params = {
        "api-key": GUARDIAN_KEY,
        "show-fields": "bodyText,thumbnail,trailText",
        "page-size": page_size,
        "section": section
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GUARDIAN_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("response", {}).get("status") == "ok":
                articles = data.get("response", {}).get("results", [])
                logger.info(f"✓ Guardian: fetched {len(articles)} articles ({section})")

                # Transform to our format
                normalized = []
                for article in articles:
                    fields = article.get("fields", {})
                    normalized.append({
                        "title": article.get("webTitle", ""),
                        "description": fields.get("trailText", ""),
                        "content": fields.get("bodyText", ""),  # Full body text
                        "url": article.get("webUrl", ""),
                        "published_at": article.get("webPublicationDate", ""),
                        "source_name": "The Guardian",
                        "image_url": fields.get("thumbnail"),
                        "category": section,
                        "source_api": "guardian"
                    })

                return normalized
            else:
                logger.error("Guardian API returned non-ok status")
                return []

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.error("Guardian rate limit exceeded (429)")
        else:
            logger.error(f"Guardian HTTP error {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"Guardian fetch error: {e}")
        return []


# ═══════════════════════════════════════════
# Multi-Source Orchestrator
# ═══════════════════════════════════════════

async def fetch_all_sources(categories: List[str] = None) -> List[Dict]:
    """
    Fetch from all available sources in parallel.
    Combines results from NewsAPI, GNews, and The Guardian.
    """
    if categories is None:
        categories = ["technology", "business", "world", "science"]

    logger.info("=" * 60)
    logger.info("Fetching from multiple news sources...")
    logger.info("=" * 60)

    all_articles = []

    # Fetch from all sources in parallel
    tasks = []

    # NewsAPI - multiple categories
    if NEWSAPI_KEY:
        for category in categories[:3]:  # Limit to 3 categories to save quota
            tasks.append(fetch_from_newsapi(category, page_size=20))

    # GNews - one main topic
    if GNEWS_KEY:
        tasks.append(fetch_from_gnews("technology", max_articles=10))

    # Guardian - main section
    if GUARDIAN_KEY:
        tasks.append(fetch_from_guardian("technology", page_size=20))

    # Execute all fetches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Fetch task failed: {result}")

    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles


# ═══════════════════════════════════════════
# Quick Single-Source Fetch (for refresh button)
# ═══════════════════════════════════════════

async def quick_fetch(max_articles: int = 30) -> List[Dict]:
    """
    Quick fetch for refresh button.
    Uses the fastest available source.
    """
    articles = []

    # Try NewsAPI first (fastest, most articles)
    if NEWSAPI_KEY:
        articles = await fetch_from_newsapi("general", page_size=max_articles)
        if articles:
            return articles

    # Try GNews
    if GNEWS_KEY:
        articles = await fetch_from_gnews("breaking-news", max_articles=10)
        if articles:
            return articles

    # Try Guardian
    if GUARDIAN_KEY:
        articles = await fetch_from_guardian("world", page_size=max_articles)
        if articles:
            return articles

    logger.warning("No articles fetched from any source")
    return []


# ═══════════════════════════════════════════
# API Health Check
# ═══════════════════════════════════════════

async def check_api_health() -> Dict[str, bool]:
    """
    Check which APIs are available and working.
    Returns dict with API name -> available status.
    """
    health = {
        "newsapi": False,
        "gnews": False,
        "guardian": False
    }

    # Check NewsAPI
    if NEWSAPI_KEY:
        try:
            articles = await fetch_from_newsapi("general", page_size=1)
            health["newsapi"] = len(articles) > 0
        except:
            pass

    # Check GNews
    if GNEWS_KEY:
        try:
            articles = await fetch_from_gnews("world", max_articles=1)
            health["gnews"] = len(articles) > 0
        except:
            pass

    # Check Guardian
    if GUARDIAN_KEY:
        try:
            articles = await fetch_from_guardian("world", page_size=1)
            health["guardian"] = len(articles) > 0
        except:
            pass

    return health
