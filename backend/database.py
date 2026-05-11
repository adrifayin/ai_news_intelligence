"""
Database layer — SQLite with SQLAlchemy ORM.
Handles schema creation, CRUD operations, and query functions.
"""

import json
import os
import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import (
    create_engine, Column, String, Text, Integer, Float, Boolean,
    DateTime, Date, Index, ForeignKey, event, text, func, case, desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news_intelligence.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Enable WAL mode for better concurrent reads ───
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ═══════════════════════════════════════════
# ORM Models
# ═══════════════════════════════════════════

class Article(Base):
    __tablename__ = "articles"

    id = Column(String(16), primary_key=True)  # SHA256(url)[:16]
    title = Column(Text, nullable=False)
    description = Column(Text)
    content = Column(Text)
    source_id = Column(String(100))
    source_name = Column(String(200))
    author = Column(String(200))
    url = Column(Text, unique=True)
    image_url = Column(Text)
    published_at = Column(DateTime)
    country = Column(String(50))
    category = Column(String(50))
    language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_articles_category", "category"),
        Index("idx_articles_published", "published_at"),
        Index("idx_articles_country", "country"),
    )


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(16), nullable=False, unique=True)
    summary = Column(Text)
    sentiment = Column(String(10))  # positive, negative, neutral
    confidence = Column(Float)
    insights = Column(Text)        # JSON array of strings
    tickers = Column(Text)         # JSON array of ticker symbols
    reading_time = Column(Integer)  # minutes
    processed_at = Column(DateTime, default=datetime.utcnow)
    # Enhanced fields from master prompt
    sentiment_score = Column(Float)            # 0.0 to 1.0
    sentiment_reasoning = Column(Text)
    story_cluster_hint = Column(String(200))
    trending_keywords = Column(Text)           # JSON array
    market_signal = Column(String(10))         # bullish, bearish, neutral
    buy_recommendation = Column(String(10))    # buy, hold, avoid
    buy_confidence = Column(Float)
    buy_reasoning = Column(Text)
    buy_target_ticker = Column(String(10))
    weather_sensitivity = Column(String(10))   # high, low, none
    weather_sectors = Column(Text)             # JSON array
    topics = Column(Text)                      # JSON array

    __table_args__ = (
        Index("idx_insights_article", "article_id"),
        Index("idx_insights_sentiment", "sentiment"),
        Index("idx_insights_cluster", "story_cluster_hint"),
        Index("idx_insights_market_signal", "market_signal"),
    )


class StoryCluster(Base):
    __tablename__ = "story_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(Text)
    article_ids = Column(Text)     # JSON array
    source_count = Column(Integer)
    is_underreported = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TickerSentiment(Base):
    __tablename__ = "ticker_sentiment"

    ticker = Column(String(10), primary_key=True)
    date = Column(Date, primary_key=True)
    mention_count = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    article_ids = Column(Text)     # JSON array

    __table_args__ = (
        Index("idx_ticker_date", "ticker", "date"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=True)
    email = Column(String(200), unique=True, nullable=True)
    display_name = Column(String(100))
    avatar_url = Column(Text)
    region = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("UserArticleInteraction", back_populates="user", cascade="all, delete-orphan")
    reading_history = relationship("UserReadingHistory", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_username", "username"),
    )


class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    weight = Column(Float, default=0.5)  # 0.0 to 1.0
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="interests")

    __table_args__ = (
        Index("idx_user_interests_user", "user_id"),
        Index("idx_user_interests_combo", "user_id", "category", unique=True),
    )


class UserArticleInteraction(Base):
    __tablename__ = "user_article_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(String(16), nullable=False)
    interaction_type = Column(String(20), nullable=False)  # like, dislike, bookmark, read, dismiss
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")

    __table_args__ = (
        Index("idx_interactions_user", "user_id"),
        Index("idx_interactions_article", "article_id"),
        Index("idx_interactions_type", "user_id", "interaction_type"),
    )


class UserReadingHistory(Base):
    __tablename__ = "user_reading_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(String(16), nullable=False)
    read_duration_seconds = Column(Integer, default=0)
    read_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reading_history")

    __table_args__ = (
        Index("idx_reading_user", "user_id"),
        Index("idx_reading_article", "user_id", "article_id"),
    )


class MLCluster(Base):
    """ML-based article clusters from advanced clustering algorithms."""
    __tablename__ = "ml_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_method = Column(String(20))  # 'dbscan', 'kmeans', 'lda'
    topic = Column(Text)
    article_ids = Column(Text)  # JSON array
    article_count = Column(Integer)
    source_count = Column(Integer)
    is_underreported = Column(Boolean, default=False)
    categories = Column(Text)  # JSON array
    keywords = Column(Text)  # JSON array of key terms
    cluster_score = Column(Float)  # Quality/coherence score
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ml_clusters_method", "cluster_method"),
        Index("idx_ml_clusters_created", "created_at"),
    )


class Topic(Base):
    """Topics discovered via LDA topic modeling."""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer)  # Topic number from LDA
    keywords = Column(Text)  # JSON array of top keywords
    article_ids = Column(Text)  # JSON array
    article_count = Column(Integer)
    topic_strength = Column(Float)  # Average probability
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_topics_strength", "topic_strength"),
        Index("idx_topics_created", "created_at"),
    )


class TrendingTopic(Base):
    """Emerging trends detected by time-series analysis."""
    __tablename__ = "trending_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False)
    recent_mentions = Column(Integer)
    growth_rate = Column(Float)  # Percentage growth
    trending_score = Column(Float)  # Combined metric
    article_ids = Column(Text)  # JSON array
    article_count = Column(Integer)
    detected_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_trending_score", "trending_score"),
        Index("idx_trending_keyword", "keyword"),
        Index("idx_trending_active", "is_active", "detected_at"),
    )


class SentimentForecast(Base):
    """Sentiment forecasts for tickers or overall market."""
    __tablename__ = "sentiment_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10))  # NULL for overall market
    forecast = Column(String(20))  # 'bullish', 'bearish', 'neutral'
    predicted_value = Column(Float)  # -1.0 to 1.0
    confidence = Column(Float)  # 0.0 to 1.0
    momentum = Column(Float)
    sma_3 = Column(Float)  # 3-day simple moving average
    data_points = Column(Integer)  # Number of historical points used
    forecast_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_forecast_ticker_date", "ticker", "forecast_date"),
        Index("idx_forecast_created", "created_at"),
    )


class ViralPrediction(Base):
    """Viral potential predictions for articles."""
    __tablename__ = "viral_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(16), nullable=False)
    viral_score = Column(Float)  # 0-100
    prediction = Column(String(10))  # 'high', 'medium', 'low'
    signals = Column(Text)  # JSON array of contributing factors
    actual_views = Column(Integer)  # To track accuracy (optional)
    predicted_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_viral_article", "article_id"),
        Index("idx_viral_score", "viral_score"),
        Index("idx_viral_prediction", "prediction"),
    )


class UserRecommendation(Base):
    """Personalized article recommendations for users."""
    __tablename__ = "user_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(String(16), nullable=False)
    recommendation_score = Column(Float)
    collab_score = Column(Float)  # Collaborative filtering component
    content_score = Column(Float)  # Content-based component
    was_viewed = Column(Boolean, default=False)
    was_clicked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_recommendations_user", "user_id", "recommendation_score"),
        Index("idx_recommendations_created", "created_at"),
    )


# ═══════════════════════════════════════════
# Database Initialization
# ═══════════════════════════════════════════

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

    # Try to add new columns if they don't exist (for existing databases)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)"))
            conn.commit()
        except Exception:
            pass  # Column likely already exists

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN region VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass

        # Migrate ai_insights table with new columns from enhanced prompt
        _new_insight_cols = [
            ("sentiment_score", "FLOAT"),
            ("sentiment_reasoning", "TEXT"),
            ("story_cluster_hint", "VARCHAR(200)"),
            ("trending_keywords", "TEXT"),
            ("market_signal", "VARCHAR(10)"),
            ("buy_recommendation", "VARCHAR(10)"),
            ("buy_confidence", "FLOAT"),
            ("buy_reasoning", "TEXT"),
            ("buy_target_ticker", "VARCHAR(10)"),
            ("weather_sensitivity", "VARCHAR(10)"),
            ("weather_sectors", "TEXT"),
            ("topics", "TEXT"),
            ("tldr", "TEXT"),
            ("key_entities", "TEXT"),
            ("impact_analysis", "TEXT"),
            ("importance_score", "INTEGER"),
            ("insight_categories", "TEXT"),
        ]
        for col_name, col_type in _new_insight_cols:
            try:
                conn.execute(text(f"ALTER TABLE ai_insights ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        # Create watchlist table if not exists
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(36) NOT NULL,
                    ticker VARCHAR(10) NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_enabled BOOLEAN DEFAULT TRUE,
                    UNIQUE(user_id, ticker)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON user_watchlist(user_id)"))
            conn.commit()
        except Exception as e:
            logger.warning(f"Watchlist table creation: {e}")

    print("Database initialized")


def get_db() -> Session:
    """Get a database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════
# Article CRUD
# ═══════════════════════════════════════════

def upsert_article(db: Session, article_data: dict) -> bool:
    """Insert article if not exists. Returns True if inserted."""
    existing = db.query(Article).filter(Article.id == article_data["id"]).first()
    if existing:
        return False

    article = Article(**article_data)
    db.add(article)
    db.commit()
    return True


def get_articles(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sentiment: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user_id: Optional[str] = None
) -> dict:
    """
    Get paginated articles with optional filters. Joins AI insights. Ranks by user preferences if user_id provided.
    FIX 2: Returns has_more flag for infinite scroll support.
    """
    query = db.query(Article, AIInsight).outerjoin(
        AIInsight, Article.id == AIInsight.article_id
    )

    if category and category != "all":
        query = query.filter(Article.category.ilike(f"%{category}%"))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Article.title.ilike(search_term)) |
            (Article.description.ilike(search_term))
        )

    if sentiment:
        query = query.filter(AIInsight.sentiment == sentiment)

    total = query.count()

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Build case statement for ranking
            whens = []
            
            # Boost by interests (+2)
            interests = [ui.category.lower() for ui in user.interests]
            if interests:
                whens.append((func.lower(Article.category).in_(interests), 2))
                
            # Boost by region (+1)
            if user.region:
                whens.append((func.lower(Article.country) == user.region.lower(), 1))
                
            if whens:
                ranking_score = case(*whens, else_=0)
                query = query.order_by(desc(ranking_score), Article.published_at.desc())
            else:
                query = query.order_by(Article.published_at.desc())
        else:
            query = query.order_by(Article.published_at.desc())
    else:
        query = query.order_by(Article.published_at.desc())

    results = query.offset((page - 1) * limit).limit(limit).all()

    articles = []
    for article, insight in results:
        article_dict = {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "content": article.content,
            "source_id": article.source_id,
            "source_name": article.source_name,
            "author": article.author,
            "url": article.url,
            "image_url": article.image_url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "country": article.country,
            "category": article.category,
            "language": article.language,
        }
        if insight:
            buy_signal = None
            if insight.buy_recommendation:
                buy_signal = {
                    "recommendation": insight.buy_recommendation,
                    "confidence": insight.buy_confidence,
                    "reasoning": insight.buy_reasoning,
                    "target_ticker": insight.buy_target_ticker,
                }
            article_dict["ai"] = {
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "confidence": insight.confidence,
                "insights": json.loads(insight.insights) if insight.insights else [],
                "tickers": json.loads(insight.tickers) if insight.tickers else [],
                "reading_time": insight.reading_time,
                "sentiment_score": insight.sentiment_score,
                "sentiment_reasoning": insight.sentiment_reasoning,
                "story_cluster_hint": insight.story_cluster_hint,
                "trending_keywords": json.loads(insight.trending_keywords) if insight.trending_keywords else [],
                "market_signal": insight.market_signal,
                "buy_signal": buy_signal,
                "weather_sensitivity": insight.weather_sensitivity,
                "weather_sectors": json.loads(insight.weather_sectors) if insight.weather_sectors else [],
                "topics": json.loads(insight.topics) if insight.topics else [],
            }
        else:
            article_dict["ai"] = None

        articles.append(article_dict)

    # FIX 2: Add has_more flag for infinite scroll
    has_more = (page * limit) < total

    return {
        "articles": articles,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "has_more": has_more,  # FIX 2: For infinite scroll
    }


def get_article_by_id(db: Session, article_id: str) -> Optional[dict]:
    """Get single article with full AI insights."""
    result = db.query(Article, AIInsight).outerjoin(
        AIInsight, Article.id == AIInsight.article_id
    ).filter(Article.id == article_id).first()

    if not result:
        return None

    article, insight = result
    article_dict = {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "content": article.content,
        "source_id": article.source_id,
        "source_name": article.source_name,
        "author": article.author,
        "url": article.url,
        "image_url": article.image_url,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "country": article.country,
        "category": article.category,
        "language": article.language,
    }
    if insight:
        buy_signal = None
        if insight.buy_recommendation:
            buy_signal = {
                "recommendation": insight.buy_recommendation,
                "confidence": insight.buy_confidence,
                "reasoning": insight.buy_reasoning,
                "target_ticker": insight.buy_target_ticker,
            }
        article_dict["ai"] = {
            "summary": insight.summary,
            "sentiment": insight.sentiment,
            "confidence": insight.confidence,
            "insights": json.loads(insight.insights) if insight.insights else [],
            "tickers": json.loads(insight.tickers) if insight.tickers else [],
            "reading_time": insight.reading_time,
            "sentiment_score": insight.sentiment_score,
            "sentiment_reasoning": insight.sentiment_reasoning,
            "story_cluster_hint": insight.story_cluster_hint,
            "trending_keywords": json.loads(insight.trending_keywords) if insight.trending_keywords else [],
            "market_signal": insight.market_signal,
            "buy_signal": buy_signal,
            "weather_sensitivity": insight.weather_sensitivity,
            "weather_sectors": json.loads(insight.weather_sectors) if insight.weather_sectors else [],
            "topics": json.loads(insight.topics) if insight.topics else [],
        }
    else:
        article_dict["ai"] = None

    return article_dict


def get_unprocessed_articles(db: Session, limit: int = 50) -> list:
    """Get articles that haven't been processed by AI yet."""
    results = db.query(Article).outerjoin(
        AIInsight, Article.id == AIInsight.article_id
    ).filter(AIInsight.id.is_(None)).limit(limit).all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "content": a.content,
            "category": a.category,
            "country": a.country,
        }
        for a in results
    ]


def get_article_count(db: Session) -> int:
    """Get total article count."""
    return db.query(Article).count()


# ═══════════════════════════════════════════
# AI Insights CRUD
# ═══════════════════════════════════════════

def save_ai_insight(db: Session, article_id: str, insight_data: dict) -> bool:
    """Save AI processing results for an article. Skip if already exists."""
    existing = db.query(AIInsight).filter(AIInsight.article_id == article_id).first()
    if existing:
        return False  # Already processed, skip

    # Extract buy_signal sub-object
    buy_signal = insight_data.get("buy_signal") or {}

    insight = AIInsight(
        article_id=article_id,
        summary=insight_data.get("summary"),
        sentiment=insight_data.get("sentiment", "neutral"),
        confidence=insight_data.get("confidence", 0.5),
        insights=json.dumps(insight_data.get("insights", [])),
        tickers=json.dumps(insight_data.get("tickers", [])),
        reading_time=insight_data.get("reading_time", 1),
        # Enhanced fields
        sentiment_score=insight_data.get("sentiment_score"),
        sentiment_reasoning=insight_data.get("sentiment_reasoning"),
        story_cluster_hint=insight_data.get("story_cluster_hint"),
        trending_keywords=json.dumps(insight_data.get("trending_keywords", [])),
        market_signal=insight_data.get("market_signal"),
        buy_recommendation=buy_signal.get("recommendation") if buy_signal else None,
        buy_confidence=buy_signal.get("confidence") if buy_signal else None,
        buy_reasoning=buy_signal.get("reasoning") if buy_signal else None,
        buy_target_ticker=buy_signal.get("target_ticker") if buy_signal else None,
        weather_sensitivity=insight_data.get("weather_sensitivity"),
        weather_sectors=json.dumps(insight_data.get("weather_sectors", [])),
        topics=json.dumps(insight_data.get("topics", [])),
    )
    db.add(insight)
    db.commit()
    return True


# ═══════════════════════════════════════════
# Stats & Aggregations
# ═══════════════════════════════════════════

def get_dashboard_stats(db: Session) -> dict:
    """Get aggregate statistics for the dashboard."""
    total_articles = db.query(Article).count()
    total_processed = db.query(AIInsight).count()

    positive = db.query(AIInsight).filter(AIInsight.sentiment == "positive").count()
    negative = db.query(AIInsight).filter(AIInsight.sentiment == "negative").count()
    neutral = db.query(AIInsight).filter(AIInsight.sentiment == "neutral").count()

    # Count unique sources
    sources_result = db.execute(
        text("SELECT COUNT(DISTINCT source_name) FROM articles WHERE source_name IS NOT NULL")
    )
    unique_sources = sources_result.scalar() or 0

    # Category breakdown
    cat_result = db.execute(
        text("SELECT category, COUNT(*) as cnt FROM articles WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC")
    )
    categories = {row[0]: row[1] for row in cat_result}

    return {
        "total_articles": total_articles,
        "total_processed": total_processed,
        "sentiment": {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        },
        "unique_sources": unique_sources,
        "categories": categories,
    }


def get_trending_keywords(db: Session, limit: int = 20) -> list:
    """
    FIX 3: Extract trending keywords from AI insights trending_keywords field (last 24 hours).
    Returns keyword with count, sorted by frequency.
    """
    # Query trending_keywords from ai_insights (last 24 hours)
    results = db.execute(
        text("""
            SELECT trending_keywords
            FROM ai_insights
            WHERE processed_at > datetime('now', '-24 hours')
              AND trending_keywords IS NOT NULL
              AND trending_keywords != '[]'
        """)
    )

    keyword_counts = {}
    for (keywords_json,) in results:
        if not keywords_json:
            continue
        try:
            keywords = json.loads(keywords_json)
            for keyword in keywords:
                if isinstance(keyword, str) and len(keyword) > 2:
                    keyword_lower = keyword.lower()
                    keyword_counts[keyword_lower] = keyword_counts.get(keyword_lower, 0) + 1
        except (json.JSONDecodeError, TypeError):
            continue

    # Sort by frequency and return top N
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"keyword": k, "count": c} for k, c in sorted_keywords]


# ═══════════════════════════════════════════
# Story Clusters
# ═══════════════════════════════════════════

def save_cluster(db: Session, cluster_data: dict) -> int:
    """Save a story cluster."""
    cluster = StoryCluster(
        topic=cluster_data["topic"],
        article_ids=json.dumps(cluster_data["article_ids"]),
        source_count=cluster_data.get("source_count", 1),
        is_underreported=cluster_data.get("is_underreported", False),
    )
    db.add(cluster)
    db.commit()
    return cluster.id


def get_clusters(db: Session, limit: int = 20) -> list:
    """Get story clusters with article details."""
    clusters = db.query(StoryCluster).order_by(
        StoryCluster.created_at.desc()
    ).limit(limit).all()

    result = []
    for c in clusters:
        article_ids = json.loads(c.article_ids) if c.article_ids else []

        # Get article titles for this cluster
        articles = db.query(Article.id, Article.title, Article.source_name).filter(
            Article.id.in_(article_ids)
        ).all() if article_ids else []

        result.append({
            "id": c.id,
            "topic": c.topic,
            "source_count": c.source_count,
            "is_underreported": c.is_underreported,
            "articles": [
                {"id": a.id, "title": a.title, "source": a.source_name}
                for a in articles
            ],
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return result


def get_story_clusters_from_ai(db: Session, limit: int = 20) -> list:
    """
    FIX 4: Get story clusters derived from AI story_cluster_hint grouping.
    Returns topic, article_count, source_count, avg_sentiment, and is_underreported flag.
    """
    results = db.execute(
        text("""
            SELECT
                ai.story_cluster_hint AS topic,
                COUNT(*) AS article_count,
                COUNT(DISTINCT a.source_id) AS source_count,
                ai.sentiment AS avg_sentiment_label,
                AVG(ai.sentiment_score) AS avg_sentiment_score,
                GROUP_CONCAT(a.id) AS article_ids,
                MAX(a.published_at) AS latest_at,
                CASE WHEN COUNT(DISTINCT a.source_id) <= 2
                     THEN 1 ELSE 0 END AS is_underreported
            FROM articles a
            JOIN ai_insights ai ON a.id = ai.article_id
            WHERE ai.story_cluster_hint IS NOT NULL
              AND ai.story_cluster_hint != ''
            GROUP BY ai.story_cluster_hint
            ORDER BY article_count DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )

    clusters = []
    for row in results:
        article_ids = row[5].split(",") if row[5] else []
        # Fetch article titles for display
        titles_result = db.execute(
            text("SELECT id, title, source_name FROM articles WHERE id IN (" +
                 ",".join([f"'{aid}'" for aid in article_ids[:10]]) + ")"
            )
        ) if article_ids else []
        articles = [
            {"id": r[0], "title": r[1], "source": r[2]}
            for r in titles_result
        ]

        # FIX 4: Determine avg_sentiment label from score
        avg_score = row[4] if row[4] else 0.5
        if avg_score > 0.6:
            avg_sentiment_label = "positive"
        elif avg_score < 0.4:
            avg_sentiment_label = "negative"
        else:
            avg_sentiment_label = "neutral"

        clusters.append({
            "topic": row[0],
            "article_count": row[1],
            "source_count": row[2],
            "avg_sentiment": avg_sentiment_label,  # FIX 4: Validated sentiment
            "avg_sentiment_score": round(avg_score, 3),
            "article_ids": article_ids[:10],
            "articles": articles,
            "latest_at": str(row[6]) if row[6] else None,
            "is_underreported": bool(row[7]),
        })

    return clusters


# ═══════════════════════════════════════════
# Ticker Sentiment
# ═══════════════════════════════════════════

def upsert_ticker_sentiment(db: Session, ticker: str, sentiment_val: float, article_id: str):
    """Update or create ticker sentiment entry for today."""
    today = date.today()
    existing = db.query(TickerSentiment).filter(
        TickerSentiment.ticker == ticker,
        TickerSentiment.date == today
    ).first()

    if existing:
        existing.mention_count += 1
        # Running average
        existing.avg_sentiment = (
            (existing.avg_sentiment * (existing.mention_count - 1) + sentiment_val) /
            existing.mention_count
        )
        ids = json.loads(existing.article_ids) if existing.article_ids else []
        if article_id not in ids:
            ids.append(article_id)
        existing.article_ids = json.dumps(ids)
    else:
        ts = TickerSentiment(
            ticker=ticker,
            date=today,
            mention_count=1,
            avg_sentiment=sentiment_val,
            article_ids=json.dumps([article_id]),
        )
        db.add(ts)

    db.commit()


def get_ticker_sentiments(db: Session) -> list:
    """Get all ticker sentiments for today, sorted by mention count."""
    today = date.today()
    results = db.query(TickerSentiment).filter(
        TickerSentiment.date == today
    ).order_by(TickerSentiment.mention_count.desc()).all()

    return [
        {
            "ticker": t.ticker,
            "mention_count": t.mention_count,
            "avg_sentiment": round(t.avg_sentiment, 3),
            "article_ids": json.loads(t.article_ids) if t.article_ids else [],
        }
        for t in results
    ]


def get_articles_by_ids(db: Session, article_ids: list) -> list:
    """Get multiple articles by their IDs."""
    if not article_ids:
        return []

    results = db.query(Article, AIInsight).outerjoin(
        AIInsight, Article.id == AIInsight.article_id
    ).filter(Article.id.in_(article_ids)).all()

    articles = []
    for article, insight in results:
        article_dict = {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "image_url": article.image_url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "source_name": article.source_name,
            "category": article.category,
        }
        if insight:
            article_dict["ai"] = {
                "summary": insight.summary,
                "sentiment": insight.sentiment,
                "confidence": insight.confidence,
            }
        articles.append(article_dict)

    return articles


# ═══════════════════════════════════════════
# Algorithm Results Storage
# ═══════════════════════════════════════════

def save_ml_cluster(db: Session, cluster_data: dict) -> int:
    """Save ML-based cluster to database."""
    cluster = MLCluster(
        cluster_method=cluster_data.get('method', 'dbscan'),
        topic=cluster_data.get('topic'),
        article_ids=json.dumps(cluster_data.get('article_ids', [])),
        article_count=cluster_data.get('article_count', 0),
        source_count=cluster_data.get('source_count', 0),
        is_underreported=cluster_data.get('is_underreported', False),
        categories=json.dumps(cluster_data.get('categories', [])),
        keywords=json.dumps(cluster_data.get('keywords', [])),
        cluster_score=cluster_data.get('cluster_score', 0.0),
    )
    db.add(cluster)
    db.commit()
    return cluster.id


def get_ml_clusters(db: Session, method: str = None, limit: int = 20) -> list:
    """Get ML-based clusters."""
    query = db.query(MLCluster)

    if method:
        query = query.filter(MLCluster.cluster_method == method)

    clusters = query.order_by(MLCluster.created_at.desc()).limit(limit).all()

    return [
        {
            'id': c.id,
            'method': c.cluster_method,
            'topic': c.topic,
            'article_ids': json.loads(c.article_ids) if c.article_ids else [],
            'article_count': c.article_count,
            'source_count': c.source_count,
            'is_underreported': c.is_underreported,
            'categories': json.loads(c.categories) if c.categories else [],
            'keywords': json.loads(c.keywords) if c.keywords else [],
            'cluster_score': c.cluster_score,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        }
        for c in clusters
    ]


def save_topic(db: Session, topic_data: dict) -> int:
    """Save discovered topic from LDA."""
    topic = Topic(
        topic_id=topic_data.get('topic_id'),
        keywords=json.dumps(topic_data.get('keywords', [])),
        article_ids=json.dumps(topic_data.get('article_ids', [])),
        article_count=topic_data.get('article_count', 0),
        topic_strength=topic_data.get('topic_strength', 0.0),
    )
    db.add(topic)
    db.commit()
    return topic.id


def get_topics(db: Session, limit: int = 10) -> list:
    """Get discovered topics."""
    topics = db.query(Topic).order_by(
        Topic.topic_strength.desc()
    ).limit(limit).all()

    return [
        {
            'id': t.id,
            'topic_id': t.topic_id,
            'keywords': json.loads(t.keywords) if t.keywords else [],
            'article_ids': json.loads(t.article_ids) if t.article_ids else [],
            'article_count': t.article_count,
            'topic_strength': t.topic_strength,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        }
        for t in topics
    ]


def save_trending_topic(db: Session, trend_data: dict) -> int:
    """Save emerging trend."""
    # Check if trend already exists (update instead)
    existing = db.query(TrendingTopic).filter(
        TrendingTopic.keyword == trend_data.get('keyword'),
        TrendingTopic.is_active == True
    ).first()

    if existing:
        existing.recent_mentions = trend_data.get('recent_mentions', 0)
        existing.growth_rate = trend_data.get('growth_rate', 0.0)
        existing.trending_score = trend_data.get('trending_score', 0.0)
        existing.article_ids = json.dumps(trend_data.get('article_ids', []))
        existing.article_count = trend_data.get('article_count', 0)
        existing.detected_at = datetime.utcnow()
        db.commit()
        return existing.id

    trend = TrendingTopic(
        keyword=trend_data.get('keyword'),
        recent_mentions=trend_data.get('recent_mentions', 0),
        growth_rate=trend_data.get('growth_rate', 0.0),
        trending_score=trend_data.get('trending_score', 0.0),
        article_ids=json.dumps(trend_data.get('article_ids', [])),
        article_count=trend_data.get('article_count', 0),
    )
    db.add(trend)
    db.commit()
    return trend.id


def get_trending_topics(db: Session, limit: int = 20, active_only: bool = True) -> list:
    """Get trending topics."""
    query = db.query(TrendingTopic)

    if active_only:
        # Get trends from last 48 hours
        cutoff = datetime.utcnow() - timedelta(hours=48)
        query = query.filter(
            TrendingTopic.is_active == True,
            TrendingTopic.detected_at >= cutoff
        )

    trends = query.order_by(TrendingTopic.trending_score.desc()).limit(limit).all()

    return [
        {
            'id': t.id,
            'keyword': t.keyword,
            'recent_mentions': t.recent_mentions,
            'growth_rate': t.growth_rate,
            'trending_score': t.trending_score,
            'article_ids': json.loads(t.article_ids) if t.article_ids else [],
            'article_count': t.article_count,
            'detected_at': t.detected_at.isoformat() if t.detected_at else None,
        }
        for t in trends
    ]


def save_sentiment_forecast(db: Session, forecast_data: dict) -> int:
    """Save sentiment forecast."""
    forecast = SentimentForecast(
        ticker=forecast_data.get('ticker'),
        forecast=forecast_data.get('forecast'),
        predicted_value=forecast_data.get('predicted_value', 0.0),
        confidence=forecast_data.get('confidence', 0.0),
        momentum=forecast_data.get('momentum', 0.0),
        sma_3=forecast_data.get('sma_3', 0.0),
        data_points=forecast_data.get('data_points', 0),
    )
    db.add(forecast)
    db.commit()
    return forecast.id


def get_sentiment_forecasts(db: Session, ticker: str = None) -> list:
    """Get recent sentiment forecasts."""
    query = db.query(SentimentForecast)

    if ticker:
        query = query.filter(SentimentForecast.ticker == ticker)

    forecasts = query.order_by(
        SentimentForecast.created_at.desc()
    ).limit(10).all()

    return [
        {
            'id': f.id,
            'ticker': f.ticker,
            'forecast': f.forecast,
            'predicted_value': f.predicted_value,
            'confidence': f.confidence,
            'momentum': f.momentum,
            'sma_3': f.sma_3,
            'data_points': f.data_points,
            'forecast_date': str(f.forecast_date),
            'created_at': f.created_at.isoformat() if f.created_at else None,
        }
        for f in forecasts
    ]


def save_viral_prediction(db: Session, prediction_data: dict) -> int:
    """Save viral potential prediction."""
    prediction = ViralPrediction(
        article_id=prediction_data.get('article_id'),
        viral_score=prediction_data.get('viral_score', 0.0),
        prediction=prediction_data.get('prediction'),
        signals=json.dumps(prediction_data.get('signals', [])),
    )
    db.add(prediction)
    db.commit()
    return prediction.id


def get_viral_predictions(db: Session, prediction_level: str = None, limit: int = 20) -> list:
    """Get viral predictions."""
    query = db.query(ViralPrediction)

    if prediction_level:
        query = query.filter(ViralPrediction.prediction == prediction_level)

    predictions = query.order_by(
        ViralPrediction.viral_score.desc()
    ).limit(limit).all()

    return [
        {
            'id': p.id,
            'article_id': p.article_id,
            'viral_score': p.viral_score,
            'prediction': p.prediction,
            'signals': json.loads(p.signals) if p.signals else [],
            'predicted_at': p.predicted_at.isoformat() if p.predicted_at else None,
        }
        for p in predictions
    ]


def save_user_recommendation(db: Session, rec_data: dict) -> int:
    """Save personalized recommendation."""
    recommendation = UserRecommendation(
        user_id=rec_data.get('user_id'),
        article_id=rec_data.get('article_id'),
        recommendation_score=rec_data.get('recommendation_score', 0.0),
        collab_score=rec_data.get('collab_score', 0.0),
        content_score=rec_data.get('content_score', 0.0),
    )
    db.add(recommendation)
    db.commit()
    return recommendation.id


def get_user_recommendations(db: Session, user_id: str, limit: int = 20) -> list:
    """Get personalized recommendations for a user."""
    recommendations = db.query(UserRecommendation).filter(
        UserRecommendation.user_id == user_id
    ).order_by(
        UserRecommendation.recommendation_score.desc()
    ).limit(limit).all()

    return [
        {
            'id': r.id,
            'article_id': r.article_id,
            'recommendation_score': r.recommendation_score,
            'collab_score': r.collab_score,
            'content_score': r.content_score,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        }
        for r in recommendations
    ]


# ═══════════════════════════════════════════
# FIX 5: Sentiment Stats & Timeline
# ═══════════════════════════════════════════

def get_sentiment_stats_24h(db: Session) -> dict:
    """
    FIX 5: Get sentiment breakdown from last 24 hours.
    Returns counts for positive, negative, neutral.
    """
    results = db.execute(
        text("""
            SELECT sentiment, COUNT(*) as count
            FROM ai_insights
            WHERE processed_at > datetime('now', '-24 hours')
              AND sentiment IN ('positive', 'negative', 'neutral')
            GROUP BY sentiment
        """)
    )

    stats = {"positive": 0, "negative": 0, "neutral": 0}
    for row in results:
        sentiment, count = row[0], row[1]
        if sentiment in stats:
            stats[sentiment] = count

    return stats


def get_sentiment_timeline(db: Session, days: int = 7) -> list:
    """
    FIX 5: Get sentiment counts over time (last N days).
    Returns daily breakdown for line chart.
    """
    results = db.execute(
        text("""
            SELECT
                DATE(ai.processed_at) as date,
                SUM(CASE WHEN ai.sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN ai.sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN ai.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral
            FROM ai_insights ai
            WHERE ai.processed_at > datetime('now', :days || ' days')
            GROUP BY DATE(ai.processed_at)
            ORDER BY date DESC
        """),
        {"days": f"-{days}"}
    )

    timeline = []
    for row in results:
        timeline.append({
            "date": str(row[0]),
            "positive": row[1],
            "negative": row[2],
            "neutral": row[3],
        })

    return timeline


def get_aggregated_insights(db: Session, limit: int = 10, category: Optional[str] = None) -> dict:
    """
    Get aggregated insights across articles, including top entities and categories.
    """
    query = db.query(AIInsight)
    if category and category != "all":
        query = query.join(Article, AIInsight.article_id == Article.id).filter(Article.category.ilike(f"%{category}%"))

    insights = query.order_by(AIInsight.processed_at.desc()).limit(100).all()

    top_entities = {}
    insight_categories = {"market": [], "tech": [], "policy": [], "risk": []}
    
    for ins in insights:
        if ins.key_entities:
            try:
                entities = json.loads(ins.key_entities)
                for ent in entities:
                    if isinstance(ent, dict) and 'name' in ent:
                        name = ent['name']
                        top_entities[name] = top_entities.get(name, 0) + 1
            except Exception:
                pass
                
        if ins.insight_categories:
            try:
                cats = json.loads(ins.insight_categories)
                for k, v in cats.items():
                    if k in insight_categories and isinstance(v, list):
                        for item in v:
                            insight_categories[k].append({"article_id": ins.article_id, "insight": item})
            except Exception:
                pass

    # Sort and limit top entities
    sorted_entities = [{"name": k, "count": v} for k, v in sorted(top_entities.items(), key=lambda item: item[1], reverse=True)[:limit]]
    
    # Keep only the top few insights per category
    for k in insight_categories:
        insight_categories[k] = insight_categories[k][:5]

    return {
        "top_entities": sorted_entities,
        "categories": insight_categories
    }
