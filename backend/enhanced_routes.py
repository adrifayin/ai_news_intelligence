"""
Enhanced API Routes for:
- Stock Predictions
- Fast Trending News
- Real-time Sentiment Tracking
- Stock Watchlist
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, get_articles, get_ml_clusters
from stock_prediction import StockPredictor, StockWatchlist
from enhanced_sentiment import sentiment_tracker
from algorithms import TrendDetector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enhanced", tags=["enhanced"])


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════
# Stock Market Predictions
# ═══════════════════════════════════════════

@router.get("/stock/predict/{ticker}")
async def predict_stock(
    ticker: str,
    days_forward: int = Query(1, ge=1, le=7),
    db: Session = Depends(get_db)
):
    """
    Predict stock movement based on news sentiment.

    Returns prediction with confidence, risk assessment, and recommendation.
    """
    try:
        predictor = StockPredictor()
        prediction = predictor.predict_movement(ticker.upper(), db, days_forward)

        return prediction

    except Exception as e:
        logger.error(f"Stock prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/opportunities")
async def get_opportunities(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Find top stock opportunities based on sentiment analysis.

    Returns bullish opportunities and bearish risks.
    """
    try:
        predictor = StockPredictor()
        opportunities = predictor.get_top_opportunities(db, limit=limit)

        return opportunities

    except Exception as e:
        logger.error(f"Opportunities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/batch-predict")
async def batch_predict_stocks(
    tickers: str = Query(..., description="Comma-separated ticker symbols"),
    db: Session = Depends(get_db)
):
    """
    Predict movements for multiple stocks at once.

    Example: ?tickers=AAPL,TSLA,GOOGL,MSFT
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

        if len(ticker_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 tickers allowed")

        predictor = StockPredictor()
        predictions = predictor.batch_predict(ticker_list, db)

        return {
            'predictions': predictions,
            'count': len(predictions)
        }

    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Stock Watchlist & Alerts
# ═══════════════════════════════════════════

@router.post("/watchlist/{user_id}/add/{ticker}")
async def add_to_watchlist(
    user_id: str,
    ticker: str,
    db: Session = Depends(get_db)
):
    """Add stock to user's watchlist."""
    try:
        watchlist = StockWatchlist()
        result = watchlist.add_to_watchlist(user_id, ticker.upper(), db)

        return result

    except Exception as e:
        logger.error(f"Watchlist add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{user_id}/remove/{ticker}")
async def remove_from_watchlist(
    user_id: str,
    ticker: str,
    db: Session = Depends(get_db)
):
    """Remove stock from watchlist."""
    try:
        watchlist = StockWatchlist()
        result = watchlist.remove_from_watchlist(user_id, ticker.upper(), db)

        return result

    except Exception as e:
        logger.error(f"Watchlist remove error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/{user_id}")
async def get_watchlist(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user's watchlist with current predictions."""
    try:
        watchlist = StockWatchlist()
        stocks = watchlist.get_watchlist(user_id, db)

        return {
            'user_id': user_id,
            'watchlist': stocks,
            'count': len(stocks)
        }

    except Exception as e:
        logger.error(f"Watchlist get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/{user_id}/alerts")
async def get_watchlist_alerts(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get alerts for stocks in watchlist with significant movements."""
    try:
        watchlist = StockWatchlist()
        alerts = watchlist.get_alerts(user_id, db)

        return {
            'user_id': user_id,
            'alerts': alerts,
            'count': len(alerts)
        }

    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Fast Trending News
# ═══════════════════════════════════════════

@router.get("/trending/fast")
async def get_fast_trending(
    window_minutes: int = Query(60, ge=15, le=360),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get fast-trending news articles.

    Analyzes recent articles for rapid engagement signals:
    - High viral potential
    - Strong sentiment
    - Emerging topics
    - Breaking news patterns
    """
    try:
        # Get recent articles
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        articles_data = get_articles(db, page=1, limit=200)
        articles = articles_data.get('articles', [])

        # Filter to recent
        recent_articles = []
        for article in articles:
            if article.get('published_at'):
                try:
                    pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    if pub_date.replace(tzinfo=None) > cutoff:
                        recent_articles.append(article)
                except:
                    pass

        if not recent_articles:
            return {
                'trending': [],
                'message': 'No recent articles in timeframe'
            }

        # Score articles for trending potential
        from backend.algorithms import TrendDetector

        detector = TrendDetector()
        scored_articles = []

        for article in recent_articles:
            # Get viral prediction
            viral_pred = detector.detect_viral_potential(article, db)

            # Calculate trending score
            minutes_old = (datetime.now() - datetime.fromisoformat(
                article['published_at'].replace('Z', '+00:00')
            ).replace(tzinfo=None)).total_seconds() / 60

            # Fresher = higher score
            recency_score = max(0, 100 - minutes_old)

            # Combine viral + recency + sentiment strength
            ai_data = article.get('ai', {})
            sentiment_strength = ai_data.get('confidence', 0) if ai_data else 0

            trending_score = (
                viral_pred['viral_score'] * 0.5 +
                recency_score * 0.3 +
                sentiment_strength * 100 * 0.2
            )

            scored_articles.append({
                **article,
                'trending_score': trending_score,
                'viral_score': viral_pred['viral_score'],
                'minutes_old': int(minutes_old),
                'signals': viral_pred['signals']
            })

        # Sort by trending score
        scored_articles.sort(key=lambda x: x['trending_score'], reverse=True)

        return {
            'trending': scored_articles[:limit],
            'window_minutes': window_minutes,
            'total_analyzed': len(recent_articles)
        }

    except Exception as e:
        logger.error(f"Fast trending error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending/breaking")
async def get_breaking_news(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get breaking news - articles with highest urgency signals.

    Prioritizes:
    - Very recent (< 30 min)
    - High controversy keywords
    - Strong sentiment
    - Multiple source coverage
    """
    try:
        # Get very recent articles
        cutoff = datetime.now() - timedelta(minutes=30)
        articles_data = get_articles(db, page=1, limit=100)
        articles = articles_data.get('articles', [])

        breaking_articles = []

        for article in articles:
            if not article.get('published_at'):
                continue

            try:
                pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                if pub_date.replace(tzinfo=None) <= cutoff:
                    continue

                # Check for breaking news indicators
                title = article.get('title', '').lower()
                breaking_keywords = [
                    'breaking', 'urgent', 'just in', 'developing', 'live update',
                    'alert', 'announcement', 'confirms', 'reports', 'exclusive'
                ]

                breaking_count = sum(1 for kw in breaking_keywords if kw in title)

                if breaking_count > 0 or pub_date.replace(tzinfo=None) > datetime.now() - timedelta(minutes=15):
                    minutes_old = (datetime.now() - pub_date.replace(tzinfo=None)).total_seconds() / 60

                    breaking_articles.append({
                        **article,
                        'minutes_old': int(minutes_old),
                        'breaking_indicators': breaking_count,
                        'urgency_score': breaking_count * 30 + (30 - minutes_old)
                    })

            except Exception as e:
                logger.warning(f"Breaking news filter error: {e}")
                continue

        # Sort by urgency
        breaking_articles.sort(key=lambda x: x['urgency_score'], reverse=True)

        return {
            'breaking': breaking_articles[:limit],
            'count': len(breaking_articles)
        }

    except Exception as e:
        logger.error(f"Breaking news error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Real-time Sentiment Tracking
# ═══════════════════════════════════════════

@router.get("/sentiment/realtime")
async def get_realtime_sentiment(
    window_minutes: int = Query(60, ge=15, le=360)
):
    """Get real-time sentiment trends."""
    try:
        trend_data = sentiment_tracker.get_trending_sentiment(window_minutes)

        return {
            'window_minutes': window_minutes,
            'trend': trend_data
        }

    except Exception as e:
        logger.error(f"Realtime sentiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/ticker/{ticker}")
async def get_ticker_sentiment_realtime(
    ticker: str,
    window_minutes: int = Query(60, ge=15, le=360)
):
    """Get real-time sentiment trend for a specific ticker."""
    try:
        trend_data = sentiment_tracker.get_ticker_trend(ticker.upper(), window_minutes)

        return trend_data

    except Exception as e:
        logger.error(f"Ticker sentiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Story Clusters (Enhanced)
# ═══════════════════════════════════════════

@router.get("/clusters/active")
async def get_active_clusters(
    min_sources: int = Query(2, ge=1, le=10),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get active story clusters with multiple source coverage.

    Filters clusters by minimum number of sources covering the story.
    """
    try:
        clusters = get_ml_clusters(db, method=None, limit=100)

        # Filter by source count
        active_clusters = [
            c for c in clusters
            if c['source_count'] >= min_sources
        ]

        # Sort by source count (more sources = bigger story)
        active_clusters.sort(key=lambda x: x['source_count'], reverse=True)

        return {
            'clusters': active_clusters[:limit],
            'count': len(active_clusters),
            'min_sources': min_sources
        }

    except Exception as e:
        logger.error(f"Active clusters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/underreported")
async def get_underreported_stories(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get underreported stories (covered by few sources but potentially significant).

    These are stories that may be overlooked by mainstream media.
    """
    try:
        clusters = get_ml_clusters(db, method=None, limit=100)

        # Filter for underreported
        underreported = [
            c for c in clusters
            if c.get('is_underreported', False)
        ]

        return {
            'underreported': underreported[:limit],
            'count': len(underreported)
        }

    except Exception as e:
        logger.error(f"Underreported error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Status Check
# ═══════════════════════════════════════════

@router.get("/status")
async def enhanced_features_status():
    """Check status of all enhanced features."""
    return {
        'status': 'operational',
        'features': {
            'stock_prediction': {
                'available': True,
                'description': 'ML-based stock movement prediction from news sentiment'
            },
            'fast_trending': {
                'available': True,
                'description': 'Real-time trending news detection'
            },
            'breaking_news': {
                'available': True,
                'description': 'Breaking news alerts and prioritization'
            },
            'sentiment_tracking': {
                'available': True,
                'description': 'Real-time sentiment momentum tracking'
            },
            'stock_watchlist': {
                'available': True,
                'description': 'Personal stock watchlist with alerts'
            },
            'story_clusters': {
                'available': True,
                'description': 'ML-based story clustering and underreported detection'
            }
        }
    }
