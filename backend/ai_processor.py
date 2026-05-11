"""
AI Processing Layer - Complete Rewrite
Uses Cohere for summarization + Groq for insights
Split into two focused calls for better reliability
"""

import json
import os
import re
import asyncio
import logging
from typing import Optional, Dict, List

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# API Configuration
# ═══════════════════════════════════════════

COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROK_API_KEY", "")  # Using GROK_API_KEY for Groq
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

COHERE_URL = "https://api.cohere.com/v1/summarize"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"


# ═══════════════════════════════════════════
# Content Extraction (FIX 1)
# ═══════════════════════════════════════════

def get_article_content(article: dict) -> Optional[str]:
    """
    Extract best available content from article.
    Handles truncation markers from various APIs.
    """
    title = str(article.get("title") or "").strip()
    description = str(article.get("description") or "").strip()
    content = str(article.get("content") or "").strip()

    # Remove common truncation markers
    content = re.sub(r'\[removed\]', '', content).strip()
    content = re.sub(r'\[\+\d+ chars\]', '', content).strip()
    content = re.sub(r'\[.*?\]$', '', content).strip()
    content = re.sub(r'ONLY AVAILABLE IN PAID PLANS', '', content).strip()

    description = re.sub(r'\[removed\]', '', description).strip()
    description = re.sub(r'\[\+\d+ chars\]', '', description).strip()

    # Score each field by usefulness
    best = ""

    if len(content) > 150:
        best = f"{title}. {content}"
    elif len(description) > 80:
        best = f"{title}. {description}"
    elif len(title) > 20:
        best = title
    else:
        logger.warning(f"No usable content for article: {title[:50]}")
        return None

    # Cap at 2000 chars — enough for AI, not too expensive
    result = best[:2000].strip()
    logger.info(f"Extracted {len(result)} chars of content")
    return result


# ═══════════════════════════════════════════
# Sentiment Validation
# ═══════════════════════════════════════════

def validate_sentiment(raw: str) -> str:
    """
    Validate sentiment string.
    Always returns exactly: "positive", "negative", or "neutral"
    """
    if not raw:
        return "neutral"

    raw = str(raw).strip().lower()

    # Exact match first
    if raw in ("positive", "negative", "neutral"):
        return raw

    # Keyword fallback
    positive_words = ["good", "gain", "rise", "up", "bull", "growth",
                      "profit", "surge", "rally", "beat", "strong",
                      "record", "high", "success", "optimistic", "breakthrough"]
    negative_words = ["bad", "loss", "fall", "down", "bear", "crash",
                      "decline", "drop", "miss", "weak", "concern",
                      "risk", "fail", "crisis", "cut", "layoff", "scandal"]

    if any(w in raw for w in positive_words):
        return "positive"
    if any(w in raw for w in negative_words):
        return "negative"

    return "neutral"


def validate_insights(insights: list) -> List[str]:
    """
    Validate and clean insights list.
    Removes generic statements and subheadings.
    """
    if not insights or not isinstance(insights, list):
        return []

    valid = []
    for insight in insights:
        if not isinstance(insight, str):
            continue

        insight = insight.strip()

        # Skip if too short
        if len(insight) < 20:
            continue

        # Skip subheadings (ends with colon)
        if insight.endswith(':'):
            continue

        # Skip generic patterns
        if re.match(r'^(Main story|Article|Title|Description|The article):', insight, re.I):
            continue

        # Skip "The article discusses..." pattern
        if insight.lower().startswith("the article"):
            continue

        # Strip bullets
        insight = insight.lstrip('•-*').strip()

        if len(insight) > 15:
            valid.append(insight)

    return valid[:5]  # Max 5 insights


# ═══════════════════════════════════════════
# JSON Parsing
# ═══════════════════════════════════════════

def safe_parse_ai_response(raw: str) -> Optional[dict]:
    """Parse AI response with error handling."""
    if not raw:
        return None

    # Strip markdown
    cleaned = raw.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try finding JSON object
    try:
        start = cleaned.index('{')
        end = cleaned.rindex('}') + 1
        return json.loads(cleaned[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    logger.error(f"Could not parse AI response: {cleaned[:200]}")
    return None


# ═══════════════════════════════════════════
# CALL 1: Summary + Sentiment (Cohere Primary)
# ═══════════════════════════════════════════

async def get_summary_and_sentiment_cohere(content: str) -> Optional[Dict]:
    """
    Use Cohere's dedicated /summarize endpoint.
    Then get sentiment from Groq/Gemini.
    """
    if not COHERE_API_KEY:
        logger.warning("COHERE_API_KEY not set")
        return None

    logger.info(f"[COHERE] Summarizing {len(content)} chars")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                COHERE_URL,
                headers={
                    "Authorization": f"Bearer {COHERE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "text": content,
                    "length": "short",
                    "format": "paragraph",
                    "extractiveness": "low",
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            data = response.json()
            summary = data.get("summary", "").strip()

            if summary and len(summary) > 30:
                logger.info(f"[COHERE] Got summary: {summary[:80]}...")

                # Now get sentiment using Groq
                sentiment_data = await get_sentiment_only(content, summary)

                return {
                    "summary": summary,
                    "sentiment": sentiment_data["sentiment"],
                    "sentiment_score": sentiment_data["sentiment_score"],
                    "sentiment_reason": sentiment_data["sentiment_reason"]
                }
            else:
                logger.warning("[COHERE] Summary too short or empty")
                return None

    except httpx.HTTPStatusError as e:
        logger.error(f"[COHERE] HTTP error {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"[COHERE] Error: {e}")
        return None


async def get_sentiment_only(content: str, summary: str) -> Dict:
    """Get sentiment for the article using Groq."""
    prompt = f"""Based on this article and its summary, determine the sentiment.

Article: {content[:500]}
Summary: {summary}

Respond with ONLY this JSON:
{{
  "sentiment": "positive or negative or neutral",
  "sentiment_score": 0.85,
  "sentiment_reason": "one sentence why"
}}

RULES:
- sentiment MUST be exactly: positive, negative, or neutral
- sentiment_score is confidence between 0.0 and 1.0
- sentiment_reason is one brief sentence"""

    raw = await call_groq_chat(prompt)
    parsed = safe_parse_ai_response(raw)

    if not parsed:
        # Fallback sentiment based on keywords
        content_lower = content.lower()
        if any(w in content_lower for w in ["record", "growth", "surge", "profit"]):
            return {"sentiment": "positive", "sentiment_score": 0.6, "sentiment_reason": "Positive keywords detected"}
        elif any(w in content_lower for w in ["loss", "decline", "crisis", "crash"]):
            return {"sentiment": "negative", "sentiment_score": 0.6, "sentiment_reason": "Negative keywords detected"}
        else:
            return {"sentiment": "neutral", "sentiment_score": 0.5, "sentiment_reason": "Mixed or unclear sentiment"}

    sentiment = validate_sentiment(parsed.get("sentiment", "neutral"))
    score = float(parsed.get("sentiment_score", 0.5))
    score = max(0.0, min(1.0, score))

    return {
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "sentiment_reason": str(parsed.get("sentiment_reason", ""))[:200]
    }


async def get_summary_and_sentiment(content: str) -> Optional[Dict]:
    """
    Main function to get summary and sentiment.
    Uses Groq (Cohere deprecated their summarize API on Sept 15, 2025).
    """
    logger.info(f"Getting summary and sentiment for {len(content)} chars")
    return await get_summary_and_sentiment_groq(content)


async def get_summary_and_sentiment_groq(content: str) -> Optional[Dict]:
    """Fallback: Use Groq for summary + sentiment."""
    prompt = f"""You are a news analyst. Read this article and respond with
ONLY a JSON object. No markdown, no explanation, nothing else.

Article:
{content}

Respond with exactly this JSON and nothing else:
{{
  "summary": "Write a 3-4 sentence executive summary explaining what happened in this article in your own words. Do not copy from the article. Start with the main event or finding, and include key context.",
  "tldr": "One-line ultra-brief summary (max 12 words)",
  "sentiment": "positive or negative or neutral",
  "sentiment_score": 0.85,
  "sentiment_reason": "one sentence why",
  "importance_score": 8
}}

IMPORTANT:
- summary MUST be 3-4 sentences you wrote yourself
- tldr MUST be very short and punchy
- sentiment MUST be exactly: positive, negative, or neutral
- sentiment_score MUST be a number between 0.0 and 1.0
- importance_score MUST be an integer between 1 and 10 based on market impact"""

    logger.info(f"[GROQ] Sending {len(content)} chars to AI")
    raw = await call_groq_chat(prompt)

    if not raw:
        logger.error("[GROQ] No response from AI")
        return None

    logger.info(f"[GROQ] Raw AI response: {raw[:200] if raw else 'EMPTY'}")

    parsed = safe_parse_ai_response(raw)

    if not parsed:
        logger.error("[GROQ] Failed to parse response")
        return None

    summary = str(parsed.get("summary") or "").strip()
    logger.info(f"[GROQ] Parsed summary: {summary[:80]}")

    # Reject bad summaries
    bad_summary = (
        not summary
        or len(summary) < 40
        or summary.endswith(":")
        or summary.lower().startswith("this article")
        or summary.lower().startswith("the article")
    )

    if bad_summary:
        logger.warning(f"[GROQ] Summary rejected: {summary[:80]}")
        return None

    sentiment = validate_sentiment(parsed.get("sentiment", "neutral"))
    importance_score = int(parsed.get("importance_score") or 5)
    importance_score = max(1, min(10, importance_score))

    score = float(parsed.get("sentiment_score", 0.5))
    score = max(0.0, min(1.0, score))

    tldr = str(parsed.get("tldr") or "")[:100]

    return {
        "summary": summary,
        "tldr": tldr,
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "sentiment_reason": str(parsed.get("sentiment_reason") or "")[:200],
        "importance_score": importance_score
    }


# ═══════════════════════════════════════════
# CALL 2: Insights + Tickers
# ═══════════════════════════════════════════

async def get_insights_and_tickers(content: str) -> Dict:
    """
    Get insights and tickers from article.
    Failure is OK - returns empty arrays.
    """
    prompt = f"""You are a financial news analyst. Read this article.
Respond with ONLY a JSON object, nothing else.

Article:
{content}

Respond with exactly this JSON:
{{
  "insights": [
    "First specific fact or finding from the article",
    "Second specific fact or finding from the article",
    "Third specific fact or finding from the article"
  ],
  "insight_categories": {{
    "market": ["Market insight 1", "Market insight 2"],
    "tech": ["Tech insight 1"],
    "policy": [],
    "risk": ["Risk insight 1"]
  }},
  "key_entities": [
    {{"name": "Apple", "type": "company", "role": "Announced new product"}},
    {{"name": "Tim Cook", "type": "person", "role": "CEO"}}
  ],
  "impact_analysis": "Brief description of who/what is impacted by this news and how.",
  "tickers": ["AAPL", "TSLA"],
  "story_cluster_hint": "Short topic label",
  "keywords": ["word1", "word2", "word3"],
  "market_signal": "bullish or bearish or neutral"
}}

RULES:
- insights: 3 specific facts from the article with real details
- insight_categories: categorize the insights or add new ones into market, tech, policy, risk arrays
- key_entities: important people, companies, or organizations mentioned
- impact_analysis: 1-2 sentences on the broader impact
- tickers: real stock symbols only, [] if none mentioned
- story_cluster_hint: 2-4 word topic eg "Fed Rate Decision"
- keywords: 3 most important words from the article"""

    logger.info("[GROQ] Getting insights and tickers")
    raw = await call_groq_chat(prompt)
    parsed = safe_parse_ai_response(raw)

    if not parsed:
        logger.warning("[GROQ] Insights call failed, using defaults")
        return {
            "insights": [],
            "insight_categories": {"market": [], "tech": [], "policy": [], "risk": []},
            "key_entities": [],
            "impact_analysis": "",
            "tickers": [],
            "story_cluster_hint": "General News",
            "keywords": [],
            "market_signal": "neutral"
        }

    insights = validate_insights(parsed.get("insights", []))

    tickers = parsed.get("tickers", [])
    if not isinstance(tickers, list):
        tickers = []
    tickers = [t.upper().strip() for t in tickers
               if isinstance(t, str)
               and re.match(r'^[A-Z]{1,5}$', t.upper().strip())]

    logger.info(f"[GROQ] Extracted {len(insights)} insights, {len(tickers)} tickers")

    return {
        "insights": insights,
        "insight_categories": parsed.get("insight_categories", {"market": [], "tech": [], "policy": [], "risk": []}),
        "key_entities": parsed.get("key_entities", []),
        "impact_analysis": str(parsed.get("impact_analysis") or ""),
        "tickers": tickers[:5],
        "story_cluster_hint": str(parsed.get("story_cluster_hint") or "General News")[:100],
        "keywords": parsed.get("keywords", [])[:10],
        "market_signal": str(parsed.get("market_signal") or "neutral")
    }


# ═══════════════════════════════════════════
# AI Provider Calls
# ═══════════════════════════════════════════

async def call_groq_chat(prompt: str) -> Optional[str]:
    """Call Groq API for chat completion."""
    # Using GROK_API_KEY from .env (Groq rebranded from Grok)
    api_key = os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROK_API_KEY or GROQ_API_KEY not set")
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "You are a professional news analyst. Always return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.error("[GROQ] Rate limit hit (429)")
        else:
            logger.error(f"[GROQ] HTTP error {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"[GROQ] Error: {e}")
        return None


# ═══════════════════════════════════════════
# Main Process Function (FIX 3)
# ═══════════════════════════════════════════

async def process_article(article: dict) -> Optional[Dict]:
    """
    Process article with TWO separate AI calls:
    1. Summary + Sentiment (MUST succeed)
    2. Insights + Tickers (can fail gracefully)
    """
    title = str(article.get("title") or "").strip()
    logger.info(f"Processing: {title[:60]}")

    # Extract content
    content = get_article_content(article)
    if not content:
        logger.warning(f"No content for: {title[:60]}")
        return None

    # Rate limiting
    await asyncio.sleep(3.0)

    # CALL 1: Summary and sentiment (retry once if fails)
    summary_data = await get_summary_and_sentiment(content)

    if not summary_data:
        # Retry once with title only
        logger.warning(f"Summary failed, retrying with title: {title[:60]}")
        await asyncio.sleep(2.0)
        summary_data = await get_summary_and_sentiment(title)

    if not summary_data:
        logger.error(f"Summary failed completely for: {title[:60]}")
        return None

    # CALL 2: Insights and tickers (failure is ok)
    try:
        await asyncio.sleep(2.0)  # Small delay between calls
        insights_data = await get_insights_and_tickers(content)
    except Exception as e:
        logger.warning(f"Insights failed for {title[:60]}: {e}")
        insights_data = {
            "insights": [],
            "insight_categories": {"market": [], "tech": [], "policy": [], "risk": []},
            "key_entities": [],
            "impact_analysis": "",
            "tickers": [],
            "story_cluster_hint": "General News",
            "keywords": [],
            "market_signal": "neutral"
        }

    # Build buy signal only if tickers found
    buy_signal = None
    if insights_data["tickers"]:
        buy_signal = {
            "recommendation": "hold",
            "confidence": summary_data["sentiment_score"],
            "reasoning": summary_data["sentiment_reason"],
            "target_ticker": insights_data["tickers"][0]
        }

    result = {
        "summary": summary_data["summary"],
        "sentiment": summary_data["sentiment"],
        "sentiment_score": summary_data["sentiment_score"],
        "sentiment_reasoning": summary_data["sentiment_reason"],
        "confidence": summary_data["sentiment_score"],  # Use sentiment score as confidence
        "insights": insights_data["insights"],
        "tickers": insights_data["tickers"],
        "reading_time": max(1, len(content) // 1000),
        "story_cluster_hint": insights_data["story_cluster_hint"],
        "trending_keywords": insights_data["keywords"],
        "market_signal": insights_data["market_signal"],
        "buy_signal": buy_signal,
        "topics": insights_data.get("topics", []),
        "weather_sensitivity": "none",
        "weather_sectors": []
    }

    logger.info(f"✓ Successfully processed: {title[:50]}")
    logger.info(f"  Summary: {result['summary'][:80]}...")
    logger.info(f"  Sentiment: {result['sentiment']} ({result['sentiment_score']})")
    logger.info(f"  Insights: {len(result['insights'])} extracted")

    return result


# ═══════════════════════════════════════════
# Batch Processing
# ═══════════════════════════════════════════

async def process_batch(articles: list, callback=None) -> list:
    """Process a batch of articles sequentially."""
    results = []
    total = len(articles)

    for i, article in enumerate(articles):
        logger.info(f"Processing {i+1}/{total}: {article.get('title', '')[:60]}...")

        result = await process_article(article)
        if result:
            result["article_id"] = article["id"]
            results.append(result)

        if callback:
            callback(i + 1, total)

    logger.info(f"Batch complete: {len(results)}/{total} processed successfully")
    return results


# ═══════════════════════════════════════════
# AI Processor Class (for compatibility)
# ═══════════════════════════════════════════

class AIProcessor:
    """Main AI processor class."""

    def __init__(self):
        self._stats = {"success": 0, "failures": 0}

    async def process_article(self, article: dict) -> Optional[dict]:
        """Process a single article."""
        result = await process_article(article)
        if result:
            self._stats["success"] += 1
        else:
            self._stats["failures"] += 1
        return result

    async def process_batch(self, articles: list, callback=None) -> list:
        """Process a batch of articles."""
        return await process_batch(articles, callback)

    @property
    def stats(self):
        return self._stats
