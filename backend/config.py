"""
Configuration Management
Centralized config with validation and environment variable loading
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration with validation."""

    # ═══════════════════════════════════════════
    # Database Configuration
    # ═══════════════════════════════════════════
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./news_intelligence.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # ═══════════════════════════════════════════
    # API Keys
    # ═══════════════════════════════════════════
    NEWSDATA_API_KEY: str = os.getenv("NEWSDATA_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    # ═══════════════════════════════════════════
    # Pipeline Configuration
    # ═══════════════════════════════════════════
    FETCH_CATEGORIES: list = os.getenv("FETCH_CATEGORIES", "technology,business,politics,science,sports").split(",")
    MAX_PAGES_PER_CATEGORY: int = int(os.getenv("MAX_PAGES_PER_CATEGORY", "2"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "20"))

    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # ═══════════════════════════════════════════
    # AI Processing
    # ═══════════════════════════════════════════
    AI_BATCH_SIZE: int = int(os.getenv("AI_BATCH_SIZE", "20"))
    AI_CONCURRENT_REQUESTS: int = int(os.getenv("AI_CONCURRENT_REQUESTS", "3"))
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "60"))

    # ═══════════════════════════════════════════
    # Server Configuration
    # ═══════════════════════════════════════════
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ═══════════════════════════════════════════
    # Feature Flags
    # ═══════════════════════════════════════════
    ENABLE_TWITTER_FETCH: bool = os.getenv("ENABLE_TWITTER_FETCH", "true").lower() == "true"
    ENABLE_AI_PROCESSING: bool = os.getenv("ENABLE_AI_PROCESSING", "true").lower() == "true"
    ENABLE_CLUSTERING: bool = os.getenv("ENABLE_CLUSTERING", "true").lower() == "true"

    # ═══════════════════════════════════════════
    # Validation
    # ═══════════════════════════════════════════
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of warnings."""
        warnings = []

        if not cls.NEWSDATA_API_KEY:
            warnings.append("⚠️  NEWSDATA_API_KEY not set - news fetching will be limited")

        if not cls.GEMINI_API_KEY and not cls.GROK_API_KEY:
            warnings.append("⚠️  No AI API keys set - will use fallback processor only")

        if not cls.ALPHA_VANTAGE_API_KEY:
            warnings.append("⚠️  ALPHA_VANTAGE_API_KEY not set - stock prices unavailable")

        if cls.DB_POOL_SIZE < 5:
            warnings.append("⚠️  DB_POOL_SIZE is low - may affect performance")

        return warnings

    @classmethod
    def print_config(cls):
        """Print current configuration (excluding secrets)."""
        print("=" * 80)
        print("CONFIGURATION")
        print("=" * 80)
        print(f"Database: {cls.DATABASE_URL.split('://')[0]}://...")
        print(f"Pool Size: {cls.DB_POOL_SIZE} (max overflow: {cls.DB_MAX_OVERFLOW})")
        print(f"Categories: {', '.join(cls.FETCH_CATEGORIES)}")
        print(f"Batch Size: {cls.BATCH_SIZE}")
        print(f"Max Retries: {cls.MAX_RETRIES}")
        print(f"Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"AI Batch Size: {cls.AI_BATCH_SIZE}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"\nAPI Keys Configured:")
        print(f"  NewsData.io: {'✓' if cls.NEWSDATA_API_KEY else '✗'}")
        print(f"  Gemini: {'✓' if cls.GEMINI_API_KEY else '✗'}")
        print(f"  Grok: {'✓' if cls.GROK_API_KEY else '✗'}")
        print(f"  Alpha Vantage: {'✓' if cls.ALPHA_VANTAGE_API_KEY else '✗'}")
        print(f"  OpenWeather: {'✓' if cls.OPENWEATHER_API_KEY else '✗'}")

        warnings = cls.validate()
        if warnings:
            print(f"\nWarnings:")
            for warning in warnings:
                print(f"  {warning}")

        print("=" * 80)


# Singleton instance
config = Config()
