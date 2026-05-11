"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class SentimentEnum(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class BuySignalData(BaseModel):
    recommendation: Optional[str] = None  # buy, hold, avoid
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    target_ticker: Optional[str] = None


class AIInsightData(BaseModel):
    summary: Optional[str] = None
    sentiment: Optional[str] = "neutral"
    confidence: Optional[float] = 0.5
    insights: list[str] = []
    tickers: list[str] = []
    reading_time: Optional[int] = 1
    # Enhanced fields
    sentiment_score: Optional[float] = None
    sentiment_reasoning: Optional[str] = None
    story_cluster_hint: Optional[str] = None
    trending_keywords: list[str] = []
    market_signal: Optional[str] = None
    buy_signal: Optional[BuySignalData] = None
    weather_sensitivity: Optional[str] = None
    weather_sectors: list[str] = []
    topics: list[str] = []


class ArticleResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    ai: Optional[AIInsightData] = None


class ArticlesPageResponse(BaseModel):
    articles: list[dict]
    total: int
    page: int
    pages: int


class StatsResponse(BaseModel):
    total_articles: int
    total_processed: int
    sentiment: dict
    unique_sources: int
    categories: dict


class ClusterResponse(BaseModel):
    id: int
    topic: Optional[str] = None
    source_count: int
    is_underreported: bool
    articles: list[dict]
    created_at: Optional[str] = None


class TickerSentimentResponse(BaseModel):
    ticker: str
    mention_count: int
    avg_sentiment: float
    article_ids: list[str] = []


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


class PipelineRunResponse(BaseModel):
    status: str
    articles_fetched: int
    articles_stored: int
    articles_processed: int
    message: str


class MarketAnalyzeRequest(BaseModel):
    market_question: str
    yes_probability: float
    avg_sentiment: Optional[str] = None
    related_summaries: Optional[str] = None


class MarketAnalyzeResponse(BaseModel):
    action: str  # buy_yes, buy_no, wait
    confidence: float
    reasoning: str
    risk_level: str  # low, medium, high
    key_factors: list[str] = []


class WeatherResponse(BaseModel):
    city: str
    temp: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    market_impact: Optional[str] = None
