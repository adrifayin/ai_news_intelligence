"""
FastAPI Application — Main entry point.
Serves REST API routes and the frontend static files.
"""

import os
import sys
import json
import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import date, datetime, timedelta

# Fix Windows console encoding for emoji
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DEBUG: Verify this file is being loaded
print("=" * 80)
print("LOADING MAIN.PY WITH ALL FIXES APPLIED")
print("=" * 80)

from dotenv import load_dotenv

# Load environment variables BEFORE importing other backend modules
load_dotenv()

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text  # For raw SQL queries

from database import (
    init_db, SessionLocal,
    get_articles, get_article_by_id, get_dashboard_stats,
    get_trending_keywords, get_clusters, get_ticker_sentiments,
    get_unprocessed_articles, get_articles_by_ids, get_article_count,
    get_story_clusters_from_ai, get_sentiment_stats_24h, get_sentiment_timeline,  # FIXES 3-5
    save_ai_insight, get_aggregated_insights,  # For reprocessing and insights
    Article, AIInsight, TickerSentiment  # Models for new endpoints
)
from models import ChatRequest, ChatResponse, PipelineRunResponse
from pipeline import run_pipeline
from ai_processor import AIProcessor
from news_fetcher import check_api_health
from market import (
    get_prediction_markets, get_sector_heatmap, get_weather_hub  # FIX 6
)
from market_service import market_service  # New Marketstack integration
from twitter_fetcher import fetch_twitter_news
from auth import router as auth_router
from algorithm_routes import router as algorithm_router
from enhanced_routes import router as enhanced_router


# ═══════════════════════════════════════════
# App Lifecycle
# ═══════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting DataStraw News Intelligence Platform...")
    init_db()

    # Run initial pipeline if database is empty
    db = SessionLocal()
    try:
        count = get_article_count(db)
        if count == 0:
            logger.info("Database empty -- running initial pipeline...")
            await run_pipeline(max_pages=1)
        else:
            logger.info(f"Database has {count} articles")
    finally:
        db.close()

    yield  # App is running

    # Shutdown
    logger.info("Shutting down...")


# ═══════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════

app = FastAPI(
    title="DataStraw News Intelligence Platform",
    description="AI-powered news analysis with market intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(algorithm_router)
app.include_router(enhanced_router)


# ═══════════════════════════════════════════
# API Routes — Articles
# ═══════════════════════════════════════════

@app.get("/api/articles")
async def api_get_articles(
    category: str = Query(None, description="Filter by category"),
    search: str = Query(None, description="Search in titles and descriptions"),
    sentiment: str = Query(None, description="Filter by sentiment"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: str = Query(None, description="User ID for personalized feed"),
):
    """Get paginated articles with optional filters."""
    db = SessionLocal()
    try:
        return get_articles(db, category=category, search=search,
                          sentiment=sentiment, page=page, limit=limit, user_id=user_id)
    finally:
        db.close()


@app.get("/api/articles/{article_id}")
async def api_get_article(article_id: str, process: bool = Query(False, description="Process with AI if not processed")):
    """Get a single article with full AI insights. Optionally process on-demand."""
    db = SessionLocal()
    try:
        article = get_article_by_id(db, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # If process=true and article has no AI insights, process it now
        if process and not article.get("ai"):
            from backend.database import Article as ArticleModel, save_ai_insight
            article_obj = db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
            if article_obj:
                ai = AIProcessor()
                article_dict = {
                    'id': article_obj.id,
                    'title': article_obj.title,
                    'description': article_obj.description or '',
                    'content': article_obj.content or article_obj.description or article_obj.title
                }
                result = await ai.process_article(article_dict)
                if result:
                    result['article_id'] = article_obj.id
                    save_ai_insight(db, article_obj.id, result)
                    db.commit()
                    # Reload article with AI insights
                    article = get_article_by_id(db, article_id)

        return article
    finally:
        db.close()


@app.post("/api/articles/batch-process")
async def api_batch_process_articles(background_tasks: BackgroundTasks, article_ids: list[str] = Query(description="List of article IDs to process")):
    """Process multiple articles with AI in background."""
    background_tasks.add_task(_process_batch, article_ids)
    return {"status": "processing", "count": len(article_ids)}


async def _process_batch(article_ids: list[str]):
    """Background task to process a batch of articles."""
    db = SessionLocal()
    try:
        ai = AIProcessor()
        from backend.database import Article as ArticleModel, save_ai_insight, AIInsight

        for article_id in article_ids:
            # Skip if already processed
            existing = db.query(AIInsight).filter(AIInsight.article_id == article_id).first()
            if existing:
                continue

            article = db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
            if not article:
                continue

            article_dict = {
                'id': article.id,
                'title': article.title,
                'description': article.description or '',
                'content': article.content or article.description or article.title
            }

            result = await ai.process_article(article_dict)
            if result:
                result['article_id'] = article.id
                save_ai_insight(db, article.id, result)
                db.commit()
                await asyncio.sleep(1)  # Rate limit
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — Dashboard
# ═══════════════════════════════════════════

@app.get("/api/stats")
async def api_get_stats():
    """Get dashboard aggregate statistics."""
    db = SessionLocal()
    try:
        return get_dashboard_stats(db)
    finally:
        db.close()


# FIX 3: Trending endpoint moved below (after bookmarks)

@app.get("/api/test-fix")
async def api_test_fix():
    """Test endpoint to verify fixes are loaded."""
    return {"status": "All fixes loaded successfully!", "fixes": [1,2,3,4,5,6,7]}


@app.get("/api/health/news-sources")
async def api_health_news_sources():
    """Check health of all news API sources."""
    health = await check_api_health()
    return {
        "sources": health,
        "available_count": sum(1 for v in health.values() if v),
        "total_count": len(health)
    }


@app.get("/api/clusters")
async def api_get_clusters(limit: int = Query(20, ge=1, le=50)):
    """FIX 4: Get story clusters from AI-generated story_cluster_hint."""
    db = SessionLocal()
    try:
        return get_story_clusters_from_ai(db, limit=limit)
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — Market Intelligence
# ═══════════════════════════════════════════

@app.get("/api/tickers")
async def api_get_tickers():
    """Get ticker sentiment data."""
    db = SessionLocal()
    try:
        return get_ticker_sentiments(db)
    finally:
        db.close()


@app.get("/api/stock/{ticker}")
async def api_get_stock(ticker: str):
    """Get real-time stock quote."""
    result = await get_stock_quote(ticker.upper())
    if not result:
        raise HTTPException(status_code=404, detail=f"Stock data not found for {ticker}")
    return result


@app.get("/api/sector-heatmap")
async def api_get_sector_heatmap():
    """Get sector sentiment heatmap data."""
    db = SessionLocal()
    try:
        tickers = get_ticker_sentiments(db)
        heatmap = await get_sector_heatmap(tickers)
        return heatmap
    finally:
        db.close()


@app.get("/api/market-mood")
async def api_get_market_mood():
    """Get aggregate market mood score."""
    db = SessionLocal()
    try:
        stats = get_dashboard_stats(db)
        sentiment = stats.get("sentiment", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        total = pos + neg + neu
        if total == 0:
            return {"score": 0.5, "label": "Neutral", "total": 0}

        # Score: 0 = very bearish, 0.5 = neutral, 1 = very bullish
        score = round((pos * 1.0 + neu * 0.5 + neg * 0.0) / total, 3)

        if score >= 0.65:
            label = "Bullish"
        elif score >= 0.55:
            label = "Slightly Bullish"
        elif score >= 0.45:
            label = "Neutral"
        elif score >= 0.35:
            label = "Slightly Bearish"
        else:
            label = "Bearish"

        return {"score": score, "label": label, "total": total}
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — Prediction Markets
# ═══════════════════════════════════════════

@app.get("/api/markets")
async def api_get_markets(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
):
    """Get prediction markets from Polymarket."""
    markets = await get_prediction_markets(limit=limit, offset=offset)

    if category:
        markets = [m for m in markets if m.get("category", "").lower() == category.lower()]

    return markets


# ═══════════════════════════════════════════
# API Routes — AI Chat
# ═══════════════════════════════════════════

@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    """Ask the News — AI chat powered by stored articles."""
    db = SessionLocal()
    try:
        # Get recent articles for context
        result = get_articles(db, page=1, limit=15)
        articles = result.get("articles", [])

        if not articles:
            return ChatResponse(
                answer="No articles available yet. Please run the pipeline first.",
                sources=[]
            )

        ai = AIProcessor()
        answer = await ai.chat_with_news(request.question, articles)

        # Return some source articles
        sources = [
            {"id": a["id"], "title": a["title"], "url": a.get("url", "")}
            for a in articles[:5]
        ]

        return ChatResponse(answer=answer, sources=sources)
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — Pipeline Control
# ═══════════════════════════════════════════

@app.post("/api/pipeline/run")
async def api_run_pipeline():
    """Manually trigger the news pipeline."""
    try:
        stats = await run_pipeline(max_pages=1)
        return PipelineRunResponse(
            status="success",
            articles_fetched=stats.get("articles_fetched", 0),
            articles_stored=stats.get("articles_stored", 0),
            articles_processed=stats.get("articles_processed", 0),
            message="Pipeline completed successfully",
        )
    except Exception as e:
        return PipelineRunResponse(
            status="error",
            articles_fetched=0,
            articles_stored=0,
            articles_processed=0,
            message=str(e),
        )


@app.post("/api/run-pipeline")
async def api_run_pipeline_alt():
    """Manually trigger the news pipeline (alternative endpoint for v2 frontend)."""
    try:
        stats = await run_pipeline(max_pages=1)
        return PipelineRunResponse(
            status="success",
            articles_fetched=stats.get("articles_fetched", 0),
            articles_stored=stats.get("articles_stored", 0),
            articles_processed=stats.get("articles_processed", 0),
            message="Pipeline completed successfully",
        )
    except Exception as e:
        import traceback
        logger.error(f"Pipeline error: {e}")
        logger.error(traceback.format_exc())
        return PipelineRunResponse(
            status="error",
            articles_fetched=0,
            articles_stored=0,
            articles_processed=0,
            message=str(e),
        )


@app.get("/api/bookmarks")
async def api_get_bookmarks(ids: str = Query("", description="Comma-separated article IDs")):
    """Get bookmarked articles by IDs."""
    if not ids:
        return []
    article_ids = [aid.strip() for aid in ids.split(",") if aid.strip()]
    db = SessionLocal()
    try:
        return get_articles_by_ids(db, article_ids)
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — Twitter/X Integration
# ═══════════════════════════════════════════

@app.get("/api/twitter/trending")
async def api_get_twitter_trending(category: str = Query(None, description="Filter by category")):
    """Fetch trending news from X/Twitter using Grok real-time API."""
    try:
        categories = [category] if category else ["technology", "business", "politics"]
        articles = await fetch_twitter_news(categories)
        return {
            "source": "X (Twitter)",
            "count": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Twitter fetch error: {e}")
        return {
            "source": "X (Twitter)",
            "count": 0,
            "articles": [],
            "error": str(e)
        }


# ═══════════════════════════════════════════
# API Routes — FIX 3: Trending Keywords (Tag Cloud)
# ═══════════════════════════════════════════

@app.get("/api/trending")
async def api_get_trending_keywords(limit: int = Query(20, ge=1, le=50)):
    """FIX 3: Get trending keywords from AI insights (last 24 hours) for tag cloud."""
    db = SessionLocal()
    try:
        return get_trending_keywords(db, limit=limit)
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — FIX 5: Sentiment Chart Data
# ═══════════════════════════════════════════

@app.get("/api/sentiment-stats")
async def api_get_sentiment_stats():
    """FIX 5: Get sentiment breakdown from last 24 hours for pie chart."""
    db = SessionLocal()
    try:
        return get_sentiment_stats_24h(db)
    finally:
        db.close()


@app.get("/api/sentiment-timeline")
async def api_get_sentiment_timeline(days: int = Query(7, ge=1, le=30)):
    """FIX 5: Get sentiment timeline over N days for line chart."""
    db = SessionLocal()
    try:
        return get_sentiment_timeline(db, days=days)
    finally:
        db.close()


# ═══════════════════════════════════════════
# API Routes — FIX 6: Markets Page Endpoints
# ═══════════════════════════════════════════

@app.get("/api/markets/tickers")
async def api_get_market_tickers():
    """Get top tickers with mentions, sentiment, and live stock prices from Marketstack."""
    db = SessionLocal()
    try:
        tickers = get_ticker_sentiments(db)

        # Get all ticker symbols
        ticker_symbols = [t["ticker"] for t in tickers[:10]]

        # Batch fetch stock quotes
        stock_quotes = await market_service.get_multiple_quotes(ticker_symbols)

        result = []
        for ticker_data in tickers[:10]:
            ticker = ticker_data["ticker"]
            stock_quote = stock_quotes.get(ticker.upper())

            # Determine sentiment label
            avg_score = ticker_data["avg_sentiment"]
            if avg_score > 0.6:
                sentiment_label = "positive"
            elif avg_score < 0.4:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

            # Determine market signal
            if avg_score > 0.65:
                market_signal = "bullish"
            elif avg_score < 0.35:
                market_signal = "bearish"
            else:
                market_signal = "neutral"

            # Buy recommendation logic
            if avg_score > 0.7 and stock_quote and stock_quote.get("change", 0) > 0:
                buy_rec = "buy"
                buy_conf = min(0.9, avg_score)
            elif avg_score < 0.3:
                buy_rec = "avoid"
                buy_conf = min(0.9, 1.0 - avg_score)
            else:
                buy_rec = "hold"
                buy_conf = 0.5

            result.append({
                "ticker": ticker,
                "price": stock_quote.get("price") if stock_quote else None,
                "change_pct": stock_quote.get("change_percent") if stock_quote else "0",
                "mention_count": ticker_data["mention_count"],
                "avg_sentiment": sentiment_label,
                "avg_sentiment_score": round(avg_score, 3),
                "market_signal": market_signal,
                "buy_recommendation": buy_rec,
                "buy_confidence": round(buy_conf, 2),
                "buy_reasoning": f"Based on {ticker_data['mention_count']} news mentions with {sentiment_label} sentiment",
            })

        return result
    except Exception as e:
        logger.error(f"Error in tickers endpoint: {e}")
        return []
    finally:
        db.close()


@app.get("/api/markets/weather")
async def api_get_market_weather():
    """FIX 6: Get weather for financial hub cities."""
    return await get_weather_hub()


@app.get("/api/markets/mood")
async def api_get_detailed_market_mood():
    """FIX 6: Get detailed market mood score with percentages."""
    db = SessionLocal()
    try:
        stats = get_sentiment_stats_24h(db)
        pos = stats.get("positive", 0)
        neg = stats.get("negative", 0)
        neu = stats.get("neutral", 0)
        total = pos + neg + neu

        if total == 0:
            return {
                "score": 50,
                "label": "Neutral",
                "positive_pct": 0,
                "negative_pct": 0,
                "neutral_pct": 0,
                "total": 0
            }

        pos_pct = round((pos / total) * 100, 1)
        neg_pct = round((neg / total) * 100, 1)
        neu_pct = round((neu / total) * 100, 1)

        # Score 0-100
        score = round(pos_pct - neg_pct + 50, 0)

        # Label
        if score >= 70:
            label = "Very Bullish"
        elif score >= 60:
            label = "Bullish"
        elif score >= 55:
            label = "Cautiously Optimistic"
        elif score >= 45:
            label = "Neutral"
        elif score >= 40:
            label = "Cautiously Pessimistic"
        elif score >= 30:
            label = "Bearish"
        else:
            label = "Very Bearish"

        return {
            "score": int(score),
            "label": label,
            "positive_pct": pos_pct,
            "negative_pct": neg_pct,
            "neutral_pct": neu_pct,
            "total": total
        }
    finally:
        db.close()


@app.get("/api/markets/leaderboard")
async def api_get_ticker_leaderboard():
    """Get top 10 most mentioned tickers with sentiment data."""
    db = SessionLocal()
    try:
        # Query ai_insights to extract and count tickers
        insights = db.query(AIInsight).all()

        ticker_mentions = {}
        ticker_sentiments = {}
        ticker_articles = {}

        for insight in insights:
            if not insight.tickers:
                continue

            try:
                tickers = json.loads(insight.tickers) if isinstance(insight.tickers, str) else insight.tickers
            except:
                continue

            if not isinstance(tickers, list):
                continue

            for ticker in tickers:
                ticker = ticker.upper().strip()
                if not ticker:
                    continue

                # Count mentions
                ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1

                # Collect sentiment scores
                if ticker not in ticker_sentiments:
                    ticker_sentiments[ticker] = []
                    ticker_articles[ticker] = []

                sentiment_score = 0.5  # Default neutral
                if insight.sentiment == "positive":
                    sentiment_score = 0.8
                elif insight.sentiment == "negative":
                    sentiment_score = 0.2

                ticker_sentiments[ticker].append(sentiment_score)
                ticker_articles[ticker].append(insight.article_id)

        # Build leaderboard
        leaderboard = []
        for ticker, count in ticker_mentions.items():
            avg_score = sum(ticker_sentiments[ticker]) / len(ticker_sentiments[ticker])

            # Determine sentiment label
            if avg_score > 0.6:
                sentiment_label = "positive"
            elif avg_score < 0.4:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

            # Buy recommendation
            if avg_score > 0.7 and count >= 3:
                buy_rec = "strong buy"
            elif avg_score > 0.6:
                buy_rec = "buy"
            elif avg_score < 0.3:
                buy_rec = "avoid"
            elif avg_score < 0.4:
                buy_rec = "sell"
            else:
                buy_rec = "hold"

            leaderboard.append({
                "ticker": ticker,
                "mention_count": count,
                "avg_sentiment": sentiment_label,
                "avg_sentiment_score": round(avg_score, 3),
                "buy_recommendation": buy_rec,
                "article_ids": ticker_articles[ticker][:5]  # First 5 articles
            })

        # Sort by mention count
        leaderboard.sort(key=lambda x: x["mention_count"], reverse=True)

        return leaderboard[:10]
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return []
    finally:
        db.close()


@app.get("/api/markets/velocity")
async def api_get_sentiment_velocity():
    """Compare sentiment velocity: today vs yesterday for each ticker."""
    db = SessionLocal()
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Get tickers for both days
        today_tickers = db.query(TickerSentiment).filter(
            TickerSentiment.date == today
        ).all()

        yesterday_tickers = db.query(TickerSentiment).filter(
            TickerSentiment.date == yesterday
        ).all()

        # Build maps
        today_map = {t.ticker: t.avg_sentiment for t in today_tickers}
        yesterday_map = {t.ticker: t.avg_sentiment for t in yesterday_tickers}

        # Calculate velocity
        velocity = []
        for ticker in today_map:
            today_score = today_map[ticker]
            yesterday_score = yesterday_map.get(ticker, 0.5)  # Default neutral if not present

            change = today_score - yesterday_score
            change_pct = round(change * 100, 1)

            if abs(change) < 0.05:
                direction = "flat"
            elif change > 0:
                direction = "up"
            else:
                direction = "down"

            velocity.append({
                "ticker": ticker,
                "today_score": round(today_score, 3),
                "yesterday_score": round(yesterday_score, 3),
                "change": round(change, 3),
                "change_pct": change_pct,
                "direction": direction
            })

        # Sort by absolute change
        velocity.sort(key=lambda x: abs(x["change"]), reverse=True)

        return velocity[:15]
    except Exception as e:
        logger.error(f"Velocity error: {e}")
        return []
    finally:
        db.close()


@app.get("/api/markets/brief")
async def api_get_market_brief():
    """Generate AI market brief from last 24h articles (cached 30 min)."""
    global _market_brief_cache, _market_brief_timestamp

    # Check cache
    now = datetime.utcnow()
    if _market_brief_cache and _market_brief_timestamp:
        cache_age = (now - _market_brief_timestamp).total_seconds()
        if cache_age < 1800:  # 30 minutes
            return _market_brief_cache

    db = SessionLocal()
    try:
        # Get articles from last 24h
        since = now - timedelta(hours=24)
        articles = db.query(Article, AIInsight).join(
            AIInsight, Article.id == AIInsight.article_id
        ).filter(
            Article.published_at >= since
        ).order_by(
            Article.published_at.desc()
        ).limit(20).all()

        if not articles:
            return {
                "brief": "No recent articles available for analysis.",
                "generated_at": now.isoformat(),
                "cached": False
            }

        # Build context
        summaries = []
        for article, insight in articles:
            summaries.append(f"• {insight.summary} (Sentiment: {insight.sentiment})")

        context = "\n".join(summaries)

        # Try to generate AI brief
        ai_brief = None
        try:
            ai = AIProcessor()
            prompt = f"""Based on these 20 recent news summaries, write a 150-word professional market brief covering:
- Dominant theme
- Top 2 positive sectors (with specific tickers if mentioned)
- Top 2 mentioned tickers
- One key risk
- Overall mood in one word at the end

Be specific. Cite tickers. Write like a Bloomberg analyst.

NEWS SUMMARIES:
{context}

MARKET BRIEF:"""

            # Try Groq only
            if ai.groq.available:
                import httpx
                try:
                    await ai.groq._rate_limit()
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{ai.groq.base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {ai.groq.api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": ai.groq.model,
                                "messages": [
                                    {"role": "system", "content": "You are a Bloomberg market analyst."},
                                    {"role": "user", "content": prompt}
                                ],
                                "temperature": 0.4,
                                "max_tokens": 400,
                            }
                        )
                        response.raise_for_status()
                        ai_brief = response.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"Groq brief failed: {e}")
        except Exception as e:
            logger.warning(f"AI brief generation failed: {e}")

        # Fallback to rule-based brief
        if not ai_brief or len(ai_brief) < 50:
            # Count sentiments
            pos_count = sum(1 for _, i in articles if i.sentiment == "positive")
            neg_count = sum(1 for _, i in articles if i.sentiment == "negative")

            mood = "Optimistic" if pos_count > neg_count else "Cautious" if neg_count > pos_count else "Mixed"

            ai_brief = f"""Market sentiment over the past 24 hours shows {pos_count} positive articles versus {neg_count} negative, indicating a {mood.lower()} outlook. Key themes include technology sector developments and business policy changes. Traders should monitor major indices for volatility. Risk factors include geopolitical tensions and regulatory changes. Overall mood: {mood}."""

        result = {
            "brief": ai_brief.strip(),
            "generated_at": now.isoformat(),
            "cached": False,
            "article_count": len(articles)
        }

        # Cache result
        _market_brief_cache = result
        _market_brief_timestamp = now

        return result
    except Exception as e:
        logger.error(f"Market brief error: {e}")
        return {
            "brief": "Unable to generate market brief at this time.",
            "generated_at": now.isoformat(),
            "cached": False,
            "error": str(e)
        }
    finally:
        db.close()


@app.get("/api/markets/divergence")
async def api_get_divergence_alerts():
    """Detect price/sentiment divergence for tickers with live price data from Marketstack."""
    db = SessionLocal()
    try:
        # Get today's ticker sentiments
        tickers = get_ticker_sentiments(db)

        # Batch fetch stock quotes
        ticker_symbols = [t["ticker"] for t in tickers[:15]]
        stock_quotes = await market_service.get_multiple_quotes(ticker_symbols)

        alerts = []

        for ticker_data in tickers[:15]:  # Check top 15
            ticker = ticker_data["ticker"]
            avg_sentiment = ticker_data["avg_sentiment"]

            # Get stock quote from batch result
            try:
                stock_quote = stock_quotes.get(ticker.upper())
                if not stock_quote:
                    continue

                price_change_pct = stock_quote.get("change_percent", 0)

                # Detect divergence
                alert = None

                # Price up but news negative
                if price_change_pct > 1.0 and avg_sentiment < 0.4:
                    alert = {
                        "ticker": ticker,
                        "price_change_pct": round(price_change_pct, 2),
                        "sentiment_score": round(avg_sentiment, 3),
                        "alert_type": "price_up_sentiment_down",
                        "alert_message": f"⚠️ {ticker} price +{price_change_pct:.1f}% but news sentiment is negative ({avg_sentiment:.2f})",
                        "severity": "warning"
                    }

                # Price down but news positive
                elif price_change_pct < -1.0 and avg_sentiment > 0.6:
                    alert = {
                        "ticker": ticker,
                        "price_change_pct": round(price_change_pct, 2),
                        "sentiment_score": round(avg_sentiment, 3),
                        "alert_type": "price_down_sentiment_up",
                        "alert_message": f"⚠️ {ticker} price {price_change_pct:.1f}% but news sentiment is positive ({avg_sentiment:.2f})",
                        "severity": "opportunity"
                    }

                if alert:
                    alerts.append(alert)

            except Exception as e:
                logger.debug(f"Divergence check failed for {ticker}: {e}")
                continue

        return alerts
    except Exception as e:
        logger.error(f"Divergence error: {e}")
        return []
    finally:
        db.close()


# Global cache for market brief
_market_brief_cache = None
_market_brief_timestamp = None


# ═══════════════════════════════════════════
# API Routes — FIX 7: Predictions Page Endpoints
# ═══════════════════════════════════════════

@app.get("/api/predictions/markets")
async def api_get_prediction_markets_enhanced(
    limit: int = Query(20, ge=1, le=50),
    category: str = Query(None, description="Filter by category")
):
    """FIX 7: Get prediction markets with related news sentiment."""
    markets = await get_prediction_markets(limit=limit)

    if category:
        markets = [m for m in markets if m.get("category", "").lower() == category.lower()]

    # Enrich with news sentiment for each market
    db = SessionLocal()
    try:
        for market in markets:
            # Find related articles by matching keywords in question with story_cluster_hint
            question_lower = market.get("question", "").lower()
            keywords = question_lower.split()[:5]  # First 5 words

            if keywords:
                # Simple keyword matching (can be enhanced)
                related_count = 0
                for kw in keywords:
                    if len(kw) > 3:  # Skip short words
                        result = db.execute(
                            text(f"SELECT COUNT(*) FROM ai_insights WHERE story_cluster_hint LIKE :kw"),
                            {"kw": f"%{kw}%"}
                        )
                        related_count += result.scalar() or 0

                market["related_article_count"] = related_count
                market["news_sentiment"] = "neutral"  # Default
                market["news_sentiment_score"] = 0.5
            else:
                market["related_article_count"] = 0
                market["news_sentiment"] = "neutral"
                market["news_sentiment_score"] = 0.5

        return markets
    finally:
        db.close()


@app.post("/api/predictions/analyze")
async def api_analyze_prediction_market(request: dict):
    """FIX 7: Analyze a prediction market with AI and give trading recommendation."""
    market_id = request.get("market_id")
    question = request.get("question", "")
    yes_probability = request.get("yes_probability", 0.5)
    related_article_ids = request.get("related_article_ids", [])

    db = SessionLocal()
    try:
        # Fetch related articles if IDs provided
        summaries = []
        avg_sentiment_score = 0.5

        if related_article_ids:
            articles = get_articles_by_ids(db, related_article_ids)
            summaries = [a.get("ai", {}).get("summary", "") for a in articles if a.get("ai")]

            # Calculate average sentiment
            scores = [a.get("ai", {}).get("sentiment_score", 0.5) for a in articles if a.get("ai")]
            if scores:
                avg_sentiment_score = sum(scores) / len(scores)

        # Determine news sentiment label
        if avg_sentiment_score > 0.6:
            news_sentiment = "positive"
        elif avg_sentiment_score < 0.4:
            news_sentiment = "negative"
        else:
            news_sentiment = "neutral"

        # Build AI prompt for trading recommendation
        summaries_text = "\n".join(summaries[:5]) if summaries else "No related news available."

        prompt = f"""You are a prediction market analyst. Given this market and related news, give a trading recommendation.

Market Question: {question}
Current YES probability: {yes_probability * 100:.1f}%
Related news sentiment: {news_sentiment} (score: {avg_sentiment_score:.2f})
News summaries:
{summaries_text}

Return ONLY this JSON (no markdown, no backticks):
{{
  "action": "buy_yes" or "buy_no" or "wait",
  "confidence": 0.0 to 1.0,
  "reasoning": "2-3 sentence explanation",
  "risk_level": "low" or "medium" or "high",
  "key_factors": ["factor1", "factor2", "factor3"],
  "price_target": "probability % target to exit position",
  "polymarket_url": "https://polymarket.com/event/{market_id or question}"
}}"""

        # Call AI processor
        ai = AIProcessor()

        # Simple logic if AI not available
        if not ai.gemini.available and not ai.grok.available:
            # Fallback logic
            if news_sentiment == "positive" and yes_probability < 0.6:
                action = "buy_yes"
                reasoning = "Positive news sentiment suggests YES probability may be undervalued."
                risk = "medium"
            elif news_sentiment == "negative" and yes_probability > 0.4:
                action = "buy_no"
                reasoning = "Negative news sentiment suggests NO probability may be undervalued."
                risk = "medium"
            else:
                action = "wait"
                reasoning = "Market probability aligns with current news sentiment. Wait for better entry."
                risk = "low"

            return {
                "action": action,
                "confidence": 0.6,
                "reasoning": reasoning,
                "risk_level": risk,
                "key_factors": ["News sentiment", "Current probability", "Market trend"],
                "price_target": "±10% from current",
                "polymarket_url": f"https://polymarket.com/event/{market_id}"
            }

        # Use AI for analysis - Groq only
        try:
            result_text = None

            # Try Groq
            if ai.groq.available:
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{ai.groq.base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {ai.groq.api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": ai.groq.model,
                                "messages": [
                                    {"role": "system", "content": "You are a prediction market analyst. Return only valid JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                "response_format": {"type": "json_object"},
                                "temperature": 0.4,
                                "max_tokens": 512,
                            }
                        )
                        response.raise_for_status()
                        result_text = response.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"Groq analysis failed: {e}")

            if result_text:
                import json
                analysis = json.loads(result_text)
                return analysis

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            # Return fallback
            return {
                "action": "wait",
                "confidence": 0.5,
                "reasoning": "Unable to analyze market at this time due to AI service limitations.",
                "risk_level": "high",
                "key_factors": ["Insufficient data", "AI unavailable"],
                "price_target": "N/A",
                "polymarket_url": f"https://polymarket.com/event/{market_id}"
            }
    finally:
        db.close()


# ═══════════════════════════════════════════
# Static Files — Serve Frontend
# ═══════════════════════════════════════════

# Determine the frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_index():
    """Serve the main dashboard page."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/market")
async def serve_market():
    """Serve the market intelligence page."""
    # Use enhanced version if available
    enhanced_file = FRONTEND_DIR / "market_enhanced.html"
    if enhanced_file.exists():
        return FileResponse(enhanced_file)
    return FileResponse(FRONTEND_DIR / "market.html")


@app.get("/predictions")
async def serve_predictions():
    """Serve the prediction markets page."""
    return FileResponse(FRONTEND_DIR / "predictions.html")


# ═══════════════════════════════════════════
# API Routes — Debug & Reprocessing
# ═══════════════════════════════════════════

@app.post("/api/test/summarize")
async def test_summarize(body: dict):
    """Test the new AI processor with sample text."""
    from backend.ai_processor import get_summary_and_sentiment

    text = body.get('text', '')
    if not text:
        return {'error': 'send { "text": "article content here" }'}

    logger.info(f"[TEST ENDPOINT] Testing AI processor with {len(text)} chars")
    result = await get_summary_and_sentiment(text)

    if result:
        logger.info(f"[TEST ENDPOINT] Success: {result.get('summary', '')[:80]}")
        return result
    else:
        logger.error("[TEST ENDPOINT] AI failed to summarize")
        return {'error': 'AI failed to summarize'}


@app.get("/api/debug/sample")
async def debug_sample():
    """Returns 3 articles with their AI insights for verification."""
    db = SessionLocal()
    try:
        results = db.query(Article, AIInsight).join(
            AIInsight, Article.id == AIInsight.article_id
        ).filter(
            AIInsight.summary != None
        ).order_by(Article.published_at.desc()).limit(3).all()

        samples = []
        for article, insight in results:
            samples.append({
                "title": article.title,
                "description": article.description,
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "sentiment_score": insight.confidence,
                "insights": json.loads(insight.insights) if insight.insights else [],
                "tickers": json.loads(insight.tickers) if insight.tickers else []
            })

        return samples
    except Exception as e:
        logger.error(f"Debug sample error: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@app.post("/api/pipeline/reprocess")
async def reprocess_all_articles(background_tasks: BackgroundTasks):
    """Delete all ai_insights and reprocess every article."""
    background_tasks.add_task(_reprocess_task)
    return {"status": "success", "message": "Reprocessing started in background"}


async def _reprocess_task():
    """Background task to reprocess all articles."""
    db = SessionLocal()
    try:
        # Delete all existing AI insights
        logger.info("Deleting all existing AI insights...")
        db.query(AIInsight).delete()
        db.commit()

        # Get all articles
        articles = db.query(Article).order_by(Article.published_at.desc()).all()
        logger.info(f"Found {len(articles)} articles to reprocess")

        ai = AIProcessor()
        processed = 0
        failed = 0

        for i, article in enumerate(articles):
            try:
                logger.info(f"Reprocessing {i+1}/{len(articles)}: {article.title[:50]}")

                article_dict = {
                    "id": article.id,
                    "title": article.title,
                    "description": article.description,
                    "content": article.content,
                }

                result = await ai.process_article(article_dict)

                if result:
                    result["article_id"] = article.id
                    save_ai_insight(db, result)
                    db.commit()
                    processed += 1
                    logger.info(f"  ✓ Processed successfully")
                else:
                    failed += 1
                    logger.warning(f"  ✗ Processing failed")

            except Exception as e:
                logger.error(f"Failed to reprocess {article.id}: {e}")
                failed += 1
                continue

        logger.info(f"Reprocessing complete: {processed} success, {failed} failed")

    except Exception as e:
        logger.error(f"Reprocessing task error: {e}")
    finally:
        db.close()


@app.get("/api/insights/aggregated")
async def api_get_aggregated_insights(limit: int = 10, category: str = "all"):
    """Get aggregated insights across articles."""
    db = SessionLocal()
    try:
        return get_aggregated_insights(db, limit, category)
    except Exception as e:
        logger.error(f"Error getting aggregated insights: {e}")
        return {"top_entities": [], "categories": {}}
    finally:
        db.close()


@app.get("/api/articles/{article_id}/insights")
async def api_get_article_insights(article_id: str):
    """Get deep insights for a specific article."""
    db = SessionLocal()
    try:
        insight = db.query(AIInsight).filter(AIInsight.article_id == article_id).first()
        if not insight:
            raise HTTPException(status_code=404, detail="Insights not found")
        
        return {
            "summary": insight.summary,
            "tldr": insight.tldr,
            "sentiment": insight.sentiment,
            "sentiment_score": insight.confidence,
            "sentiment_reasoning": insight.sentiment_reasoning,
            "importance_score": insight.importance_score,
            "insights": json.loads(insight.insights) if insight.insights else [],
            "insight_categories": json.loads(insight.insight_categories) if insight.insight_categories else {},
            "key_entities": json.loads(insight.key_entities) if insight.key_entities else [],
            "impact_analysis": insight.impact_analysis,
            "tickers": json.loads(insight.tickers) if insight.tickers else [],
            "market_signal": insight.market_signal,
            "topics": json.loads(insight.topics) if insight.topics else [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()


# Mount static files (CSS, JS) — this must be AFTER route definitions
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
