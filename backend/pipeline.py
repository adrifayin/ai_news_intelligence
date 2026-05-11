"""
Data Pipeline -- Fetches news from NewsData.io, cleans, deduplicates,
and stores articles. Triggers AI processing for new articles.
"""

import hashlib
import os
import re
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import httpx
from bs4 import BeautifulSoup

from backend.database import (
    SessionLocal, upsert_article, get_unprocessed_articles,
    save_ai_insight, upsert_ticker_sentiment, save_cluster, get_article_count
)
from backend.ai_processor import AIProcessor, get_article_content
from backend.twitter_fetcher import fetch_twitter_news
from backend.news_fetcher import fetch_all_sources, quick_fetch

# Legacy NewsData config (kept for backwards compatibility)
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"
CATEGORIES = os.getenv("FETCH_CATEGORIES", "technology,business,world,science").split(",")


# ═══════════════════════════════════════════
# News Fetching
# ═══════════════════════════════════════════

async def fetch_news_page(
    category: Optional[str] = None,
    page_token: Optional[str] = None,
    language: str = "en"
) -> dict:
    """
    Fetch a single page of news from NewsData.io.
    Returns: { results: [...], nextPage: "token" or None }
    """
    params = {
        "apikey": NEWSDATA_API_KEY,
        "language": language,
    }
    if category:
        params["category"] = category
    if page_token:
        params["page"] = page_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(3):  # Retry with backoff
            try:
                response = await client.get(NEWSDATA_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "success":
                    return {
                        "results": data.get("results", []),
                        "next_page": data.get("nextPage"),
                        "total_results": data.get("totalResults", 0),
                    }
                else:
                    error_msg = data.get("results", {}).get("message", "Unknown error")
                    logger.warning(f"NewsData.io API error: {error_msg}")
                    return {"results": [], "next_page": None, "total_results": 0}

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.info(f"Rate limited. Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.warning(f"HTTP error: {e}")
                    return {"results": [], "next_page": None, "total_results": 0}

            except httpx.RequestError as e:
                logger.warning(f"Request error: {e}")
                wait = 2 ** attempt
                await asyncio.sleep(wait)

    return {"results": [], "next_page": None, "total_results": 0}


async def fetch_all_news(
    categories: list = None,
    max_pages_per_category: int = 2
) -> list:
    """
    Fetch news across multiple categories with pagination.
    Respects free tier limits (~200 credits/day, 1 credit per call).
    """
    if not NEWSDATA_API_KEY:
        logger.warning("NEWSDATA_API_KEY not set. Skipping news fetch.")
        return []

    if categories is None:
        categories = CATEGORIES

    all_articles = []

    for category in categories:
        logger.info(f"Fetching {category} news...")
        page_token = None

        for page_num in range(max_pages_per_category):
            result = await fetch_news_page(category=category, page_token=page_token)
            articles = result.get("results", [])

            if not articles:
                break

            for raw_article in articles:
                raw_article["_category"] = category

            all_articles.extend(articles)
            print(f"   Page {page_num + 1}: {len(articles)} articles")

            page_token = result.get("next_page")
            if not page_token:
                break

            # Small delay between pages
            await asyncio.sleep(1)

        # Delay between categories
        await asyncio.sleep(0.5)

    logger.info(f"Total fetched: {len(all_articles)} articles across {len(categories)} categories")
    return all_articles


# ═══════════════════════════════════════════
# Data Cleaning & Validation
# ═══════════════════════════════════════════

def generate_article_id(url: str) -> str:
    """Generate deterministic ID from article URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def clean_article(raw: dict) -> Optional[dict]:
    """
    Clean and validate a raw article from multiple sources.
    Returns None if article is invalid.
    """
    # Require at minimum a title and URL
    title = raw.get("title")
    url = raw.get("url") or raw.get("link")  # Support both formats

    if not title or not url:
        return None

    # Skip articles with [Removed] titles
    if title.strip().lower() in ("[removed]", ""):
        return None

    # Clean text fields
    description = strip_html(raw.get("description", "") or "")
    content = strip_html(raw.get("content", "") or "")

    # Parse published date
    published_at = None
    pub_date_str = raw.get("published_at") or raw.get("pubDate")  # Support both formats
    if pub_date_str:
        try:
            published_at = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                published_at = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                published_at = datetime.utcnow()

    # Extract category (NewsData.io returns list)
    categories = raw.get("category", [])
    category = raw.get("_category", "")
    if isinstance(categories, list) and categories:
        category = categories[0]
    elif isinstance(categories, str):
        category = categories

    # Extract country
    country_list = raw.get("country", [])
    country = ""
    if isinstance(country_list, list) and country_list:
        country = country_list[0]
    elif isinstance(country_list, str):
        country = country_list

    return {
        "id": generate_article_id(url),
        "title": title.strip()[:500],
        "description": description[:2000] if description else None,
        "content": content[:10000] if content else None,
        "source_id": raw.get("source_id", ""),
        "source_name": raw.get("source_name") or raw.get("source_id", "Unknown"),
        "author": (", ".join(raw.get("creator", [])) if isinstance(raw.get("creator"), list) else raw.get("creator", "")) or None,
        "url": url,
        "image_url": raw.get("image_url"),
        "published_at": published_at,
        "country": country.upper() if country else None,
        "category": category.lower() if category else None,
        "language": raw.get("language", "en"),
    }


def deduplicate_articles(articles: list) -> list:
    """Remove duplicates based on article ID."""
    seen = set()
    unique = []
    for article in articles:
        if article["id"] not in seen:
            seen.add(article["id"])
            unique.append(article)
    return unique


# ═══════════════════════════════════════════
# Story Clustering (Simple keyword-based)
# ═══════════════════════════════════════════

def cluster_articles(articles: list) -> list:
    """
    Simple clustering: group articles with similar titles.
    Uses keyword overlap to detect related stories.
    """
    if not articles:
        return []

    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "not", "as",
        "it", "its", "this", "that", "has", "have", "had", "new", "says",
    }

    def extract_keywords(title: str) -> set:
        words = re.findall(r'\b[a-z]{3,}\b', title.lower())
        return {w for w in words if w not in stop_words}

    # Build keyword sets for each article
    article_keywords = []
    for article in articles:
        keywords = extract_keywords(article.get("title", ""))
        article_keywords.append((article["id"], keywords, article.get("title", "")))

    # Find clusters by keyword overlap
    clusters = []
    used = set()

    for i, (id1, kw1, title1) in enumerate(article_keywords):
        if id1 in used:
            continue

        cluster_ids = [id1]
        used.add(id1)

        for j, (id2, kw2, title2) in enumerate(article_keywords):
            if i == j or id2 in used:
                continue

            # Check if articles share significant keywords
            overlap = kw1 & kw2
            if len(overlap) >= 2:
                cluster_ids.append(id2)
                used.add(id2)

        if len(cluster_ids) >= 2:
            # Determine topic from shared keywords
            all_kw = set()
            for aid in cluster_ids:
                for _, kw, _ in article_keywords:
                    all_kw |= kw
                    break

            topic_words = list(kw1)[:4]
            topic = " ".join(w.capitalize() for w in topic_words) if topic_words else "Related Stories"

            clusters.append({
                "topic": topic,
                "article_ids": cluster_ids,
                "source_count": len(cluster_ids),
                "is_underreported": len(cluster_ids) <= 2,
            })

    return clusters


# ═══════════════════════════════════════════
# Pipeline Orchestrator
# ═══════════════════════════════════════════

async def run_pipeline(categories: list = None, max_pages: int = 2) -> dict:
    """
    Full pipeline: fetch → clean → deduplicate → store → AI process.
    Returns stats about the pipeline run.
    """
    logger.info("="*60)
    logger.info("Starting News Intelligence Pipeline")
    logger.info("="*60)

    stats = {
        "articles_fetched": 0,
        "articles_stored": 0,
        "articles_processed": 0,
        "clusters_created": 0,
    }

    # Step 1: Fetch news from multiple sources (NewsAPI, GNews, Guardian)
    logger.info("Step 1: Fetching news from multiple sources...")
    raw_articles = await fetch_all_sources(categories=categories)

    stats["articles_fetched"] = len(raw_articles)

    if not raw_articles:
        logger.warning("No articles fetched. Check your API keys.")
        return stats

    # Step 2: Clean & validate
    logger.info("Step 2: Cleaning & validating...")
    cleaned = []
    for raw in raw_articles:
        article = clean_article(raw)
        if article:
            cleaned.append(article)
    print(f"   {len(cleaned)}/{len(raw_articles)} articles passed validation")

    # Step 3: Deduplicate
    logger.info("Step 3: Deduplicating...")
    unique = deduplicate_articles(cleaned)
    print(f"   {len(unique)} unique articles (removed {len(cleaned) - len(unique)} duplicates)")

    # Step 4: Store in database
    logger.info("Step 4: Storing in database...")
    db = SessionLocal()
    try:
        stored_count = 0
        for article in unique:
            if upsert_article(db, article):
                stored_count += 1
        stats["articles_stored"] = stored_count
        print(f"   {stored_count} new articles stored")

        # Step 5: Cluster articles
        logger.info("Step 5: Clustering stories...")
        clusters = cluster_articles(unique)
        for cluster in clusters:
            save_cluster(db, cluster)
        stats["clusters_created"] = len(clusters)
        print(f"   {len(clusters)} story clusters created")

        # Step 6: AI Processing (with content validation)
        logger.info("Step 6: AI Processing...")
        unprocessed = get_unprocessed_articles(db, limit=30)
        if unprocessed:
            # Filter out articles with no usable content
            processable = []
            for article in unprocessed:
                # article is already a dict from get_unprocessed_articles
                # Check if article has enough content
                if get_article_content(article):
                    processable.append(article)
                else:
                    logger.warning(f"Skipping article with no content: {article['title'][:50]}")

            logger.info(f"Processing {len(processable)}/{len(unprocessed)} articles with usable content")

            ai = AIProcessor()
            results = await ai.process_batch(processable)

            for result in results:
                article_id = result.pop("article_id")
                save_ai_insight(db, article_id, result)

                # Save ticker sentiments
                sentiment_val = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}.get(
                    result.get("sentiment", "neutral"), 0.0
                )
                for ticker in result.get("tickers", []):
                    upsert_ticker_sentiment(db, ticker, sentiment_val, article_id)

            stats["articles_processed"] = len(results)
            print(f"   {len(results)} articles processed by AI")
        else:
            print("   No unprocessed articles found")

    finally:
        db.close()

    logger.info("="*60)
    logger.info("Pipeline complete!")
    logger.info(f"Fetched: {stats['articles_fetched']} | Stored: {stats['articles_stored']} | Processed: {stats['articles_processed']} | Clusters: {stats['clusters_created']}")
    logger.info("="*60)

    return stats
