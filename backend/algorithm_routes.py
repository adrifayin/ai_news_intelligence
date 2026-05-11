"""
API Routes for Algorithm Services
Provides endpoints for recommendations, clustering, trends, and forecasts.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database import (
    SessionLocal,
    get_articles,
    get_ml_clusters,
    get_topics,
    get_trending_topics,
    get_sentiment_forecasts,
    get_viral_predictions,
    get_user_recommendations,
    save_ml_cluster,
    save_topic,
    save_trending_topic,
    save_sentiment_forecast,
    save_viral_prediction,
    save_user_recommendation,
)
from backend.algorithms import (
    NewsRecommender,
    AdvancedClusterer,
    TrendDetector,
    AlgorithmOrchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/algorithms", tags=["algorithms"])


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════
# Personalized Recommendations
# ═══════════════════════════════════════════

@router.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get personalized article recommendations for a user.

    Uses hybrid collaborative + content-based filtering.
    """
    try:
        # Get recent articles
        articles_data = get_articles(db, page=1, limit=200)
        articles = articles_data.get('articles', [])

        if not articles:
            return {
                'user_id': user_id,
                'recommendations': [],
                'message': 'No articles available'
            }

        # Generate recommendations
        recommender = NewsRecommender()
        recommendations = recommender.recommend(user_id, articles, db, top_k=limit)

        # Save to database for analytics
        for rec in recommendations[:10]:  # Save top 10
            try:
                save_user_recommendation(db, {
                    'user_id': user_id,
                    'article_id': rec['id'],
                    'recommendation_score': rec.get('recommendation_score', 0),
                    'collab_score': rec.get('collab_score', 0),
                    'content_score': rec.get('content_score', 0),
                })
            except:
                pass  # Skip if already exists

        return {
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'algorithm': 'hybrid_collab_content',
        }

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}/history")
async def get_recommendation_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get historical recommendations for a user."""
    try:
        recommendations = get_user_recommendations(db, user_id, limit=limit)

        return {
            'user_id': user_id,
            'history': recommendations,
            'count': len(recommendations),
        }

    except Exception as e:
        logger.error(f"Recommendation history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Advanced Clustering
# ═══════════════════════════════════════════

@router.post("/cluster")
async def cluster_articles(
    method: str = Query('dbscan', regex='^(dbscan|kmeans)$'),
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Run ML-based clustering on recent articles.

    Methods:
    - dbscan: Density-based clustering (auto-detects number of clusters)
    - kmeans: K-means clustering (fixed number of clusters)
    """
    try:
        # Get articles
        articles_data = get_articles(db, page=1, limit=200)
        articles = articles_data.get('articles', [])

        if not articles:
            return {
                'clusters': [],
                'message': 'No articles available for clustering'
            }

        # Run clustering
        clusterer = AdvancedClusterer()
        clusters = clusterer.cluster_articles_ml(articles, method=method)

        # Save to database
        if save_results:
            for cluster in clusters:
                cluster_with_method = {**cluster, 'method': method}
                save_ml_cluster(db, cluster_with_method)

        return {
            'method': method,
            'clusters': clusters,
            'cluster_count': len(clusters),
            'articles_clustered': sum(c['article_count'] for c in clusters),
        }

    except Exception as e:
        logger.error(f"Clustering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters")
async def list_clusters(
    method: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get stored ML clusters."""
    try:
        clusters = get_ml_clusters(db, method=method, limit=limit)

        return {
            'clusters': clusters,
            'count': len(clusters),
        }

    except Exception as e:
        logger.error(f"Cluster retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Topic Modeling
# ═══════════════════════════════════════════

@router.post("/topics")
async def discover_topics(
    n_topics: int = Query(10, ge=3, le=20),
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Discover latent topics using LDA (Latent Dirichlet Allocation).

    Extracts hidden themes and patterns from article corpus.
    """
    try:
        # Get articles
        articles_data = get_articles(db, page=1, limit=300)
        articles = articles_data.get('articles', [])

        if len(articles) < 10:
            return {
                'topics': [],
                'message': 'Insufficient articles for topic modeling (minimum 10 required)'
            }

        # Run topic modeling
        clusterer = AdvancedClusterer()
        topics = clusterer.topic_modeling(articles, n_topics=n_topics)

        # Save to database
        if save_results:
            for topic in topics:
                save_topic(db, topic)

        return {
            'topics': topics,
            'topic_count': len(topics),
            'n_topics_requested': n_topics,
            'algorithm': 'lda',
        }

    except Exception as e:
        logger.error(f"Topic modeling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def list_topics(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get discovered topics."""
    try:
        topics = get_topics(db, limit=limit)

        return {
            'topics': topics,
            'count': len(topics),
        }

    except Exception as e:
        logger.error(f"Topic retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Trend Detection
# ═══════════════════════════════════════════

@router.post("/trends/detect")
async def detect_trends(
    window_hours: int = Query(48, ge=6, le=168),
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Detect emerging trends using time-series analysis.

    Analyzes keyword frequency over time to identify rising topics.
    """
    try:
        # Get articles
        articles_data = get_articles(db, page=1, limit=500)
        articles = articles_data.get('articles', [])

        if not articles:
            return {
                'trends': [],
                'message': 'No articles available for trend detection'
            }

        # Detect trends
        detector = TrendDetector()
        trends = detector.detect_emerging_trends(articles, window_hours=window_hours)

        # Save to database
        if save_results:
            for trend in trends:
                save_trending_topic(db, trend)

        return {
            'trends': trends,
            'trend_count': len(trends),
            'window_hours': window_hours,
            'algorithm': 'time_series_growth_rate',
        }

    except Exception as e:
        logger.error(f"Trend detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def list_trends(
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get trending topics."""
    try:
        trends = get_trending_topics(db, limit=limit, active_only=active_only)

        return {
            'trends': trends,
            'count': len(trends),
        }

    except Exception as e:
        logger.error(f"Trend retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Sentiment Forecasting
# ═══════════════════════════════════════════

@router.post("/forecast/sentiment")
async def forecast_sentiment(
    ticker: Optional[str] = Query(None),
    days_back: int = Query(7, ge=3, le=30),
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Forecast sentiment trends using time-series analysis.

    Predicts future sentiment direction based on historical patterns.
    """
    try:
        # Generate forecast
        detector = TrendDetector()
        forecast = detector.forecast_sentiment(db, ticker=ticker, days_back=days_back)

        # Save to database
        if save_results:
            save_sentiment_forecast(db, {
                'ticker': ticker,
                **forecast
            })

        return {
            'ticker': ticker or 'overall_market',
            'forecast': forecast,
            'days_analyzed': days_back,
        }

    except Exception as e:
        logger.error(f"Sentiment forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/sentiment")
async def list_forecasts(
    ticker: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get recent sentiment forecasts."""
    try:
        forecasts = get_sentiment_forecasts(db, ticker=ticker)

        return {
            'ticker': ticker,
            'forecasts': forecasts,
            'count': len(forecasts),
        }

    except Exception as e:
        logger.error(f"Forecast retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Viral Potential Prediction
# ═══════════════════════════════════════════

@router.post("/viral/predict")
async def predict_viral(
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Predict viral potential for recent articles.

    Analyzes multiple signals to identify articles likely to go viral.
    """
    try:
        # Get recent articles
        articles_data = get_articles(db, page=1, limit=100)
        articles = articles_data.get('articles', [])

        if not articles:
            return {
                'predictions': [],
                'message': 'No articles available'
            }

        # Predict viral potential
        detector = TrendDetector()
        predictions = []

        for article in articles:
            prediction = detector.detect_viral_potential(article, db)
            predictions.append(prediction)

            # Save high/medium predictions
            if save_results and prediction['prediction'] in ['high', 'medium']:
                save_viral_prediction(db, prediction)

        # Sort by score
        predictions.sort(key=lambda x: x['viral_score'], reverse=True)

        return {
            'predictions': predictions[:20],
            'total_analyzed': len(articles),
            'high_potential': len([p for p in predictions if p['prediction'] == 'high']),
            'medium_potential': len([p for p in predictions if p['prediction'] == 'medium']),
        }

    except Exception as e:
        logger.error(f"Viral prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/viral/predictions")
async def list_viral_predictions(
    prediction_level: Optional[str] = Query(None, regex='^(high|medium|low)$'),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get viral predictions."""
    try:
        predictions = get_viral_predictions(db, prediction_level=prediction_level, limit=limit)

        return {
            'predictions': predictions,
            'count': len(predictions),
        }

    except Exception as e:
        logger.error(f"Viral prediction retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Run All Algorithms
# ═══════════════════════════════════════════

@router.post("/run-all")
async def run_all_algorithms(
    save_results: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Run all algorithms in one go.

    Executes:
    - ML clustering
    - Topic modeling
    - Trend detection
    - Sentiment forecasting
    - Viral prediction

    Returns comprehensive analysis.
    """
    try:
        orchestrator = AlgorithmOrchestrator()
        results = orchestrator.run_all_algorithms(db)

        # Save results to database
        if save_results:
            # Save clusters
            for cluster in results.get('clusters', []):
                save_ml_cluster(db, {**cluster, 'method': 'dbscan'})

            # Save topics
            for topic in results.get('topics', []):
                save_topic(db, topic)

            # Save trends
            for trend in results.get('trends', []):
                save_trending_topic(db, trend)

            # Save forecasts
            overall_forecast = results.get('forecasts', {}).get('overall')
            if overall_forecast:
                save_sentiment_forecast(db, {
                    'ticker': None,
                    **overall_forecast
                })

            # Save viral predictions
            for viral in results.get('viral_candidates', []):
                save_viral_prediction(db, viral)

        return {
            'status': 'success',
            'results': results,
            'summary': {
                'clusters': len(results.get('clusters', [])),
                'topics': len(results.get('topics', [])),
                'trends': len(results.get('trends', [])),
                'viral_candidates': len(results.get('viral_candidates', [])),
            }
        }

    except Exception as e:
        logger.error(f"Algorithm orchestration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Algorithm Status & Metadata
# ═══════════════════════════════════════════

@router.get("/status")
async def algorithm_status(db: Session = Depends(get_db)):
    """Get status of all algorithm systems."""
    try:
        return {
            'status': 'operational',
            'algorithms': {
                'recommendations': {
                    'available': True,
                    'method': 'hybrid_collaborative_content',
                },
                'clustering': {
                    'available': True,
                    'methods': ['dbscan', 'kmeans'],
                },
                'topic_modeling': {
                    'available': True,
                    'method': 'lda',
                },
                'trend_detection': {
                    'available': True,
                    'method': 'time_series_growth',
                },
                'sentiment_forecast': {
                    'available': True,
                    'method': 'sma_momentum',
                },
                'viral_prediction': {
                    'available': True,
                    'method': 'multi_signal',
                },
            }
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
