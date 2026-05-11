"""
Health Monitoring and System Status
Provides health checks for all system components
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from backend.config import config
from backend.db_manager import db_manager
from backend.http_client import newsdata_client
from backend.logger import get_logger
from backend.database import Article, AIInsight

logger = get_logger(__name__)


class HealthMonitor:
    """Monitor health of system components."""

    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity and status."""
        try:
            health = db_manager.health_check()
            pool_stats = db_manager.get_pool_stats()

            with db_manager.get_session() as session:
                article_count = session.query(Article).count()
                insight_count = session.query(AIInsight).count()

            return {
                "status": "healthy",
                "connectivity": health.get("status"),
                "pool_stats": pool_stats,
                "article_count": article_count,
                "insight_count": insight_count,
                "processed_percentage": round(
                    (insight_count / article_count * 100) if article_count > 0 else 0,
                    2
                ),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    @staticmethod
    async def check_newsdata_api() -> Dict[str, Any]:
        """Check NewsData.io API availability."""
        if not config.NEWSDATA_API_KEY:
            return {
                "status": "not_configured",
                "message": "API key not set",
            }

        try:
            # Make a minimal request
            params = {
                "apikey": config.NEWSDATA_API_KEY,
                "language": "en",
                "category": "technology",
            }

            data = await newsdata_client.get(
                "https://newsdata.io/api/1/latest",
                params=params,
                api_name="NewsData.io"
            )

            if data.get("status") == "success":
                return {
                    "status": "healthy",
                    "available_results": data.get("totalResults", 0),
                }
            else:
                return {
                    "status": "error",
                    "message": data.get("results", {}).get("message", "Unknown error"),
                }

        except Exception as e:
            logger.error(f"NewsData.io health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    @staticmethod
    def check_api_keys() -> Dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "newsdata": bool(config.NEWSDATA_API_KEY),
            "gemini": bool(config.GEMINI_API_KEY),
            "grok": bool(config.GROK_API_KEY),
            "alpha_vantage": bool(config.ALPHA_VANTAGE_API_KEY),
            "openweather": bool(config.OPENWEATHER_API_KEY),
        }

    @staticmethod
    def check_system_config() -> Dict[str, Any]:
        """Check system configuration."""
        return {
            "database_type": config.DATABASE_URL.split("://")[0],
            "pool_size": config.DB_POOL_SIZE,
            "batch_size": config.BATCH_SIZE,
            "max_retries": config.MAX_RETRIES,
            "categories": config.FETCH_CATEGORIES,
            "twitter_enabled": config.ENABLE_TWITTER_FETCH,
            "ai_enabled": config.ENABLE_AI_PROCESSING,
            "clustering_enabled": config.ENABLE_CLUSTERING,
        }

    @staticmethod
    async def full_health_check() -> Dict[str, Any]:
        """
        Run comprehensive health check on all components.

        Returns:
            Health status dictionary
        """
        logger.info("Running full health check...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
        }

        # Check database
        db_health = await HealthMonitor.check_database()
        results["database"] = db_health
        if db_health["status"] != "healthy":
            results["overall_status"] = "degraded"

        # Check NewsData.io API
        newsdata_health = await HealthMonitor.check_newsdata_api()
        results["newsdata_api"] = newsdata_health
        if newsdata_health["status"] not in ["healthy", "not_configured"]:
            results["overall_status"] = "degraded"

        # Check API keys
        results["api_keys"] = HealthMonitor.check_api_keys()

        # Check system config
        results["system_config"] = HealthMonitor.check_system_config()

        # Configuration warnings
        warnings = config.validate()
        if warnings:
            results["warnings"] = warnings

        logger.info(f"Health check complete: {results['overall_status']}")
        return results

    @staticmethod
    def print_health_report(health: Dict[str, Any]):
        """Print formatted health report."""
        logger.info("=" * 80)
        logger.info("SYSTEM HEALTH REPORT")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {health['timestamp']}")
        logger.info(f"Overall Status: {health['overall_status'].upper()}")
        logger.info("")

        # Database
        db = health.get("database", {})
        logger.info("Database:")
        logger.info(f"  Status: {db.get('status', 'unknown')}")
        logger.info(f"  Articles: {db.get('article_count', 0)}")
        logger.info(f"  AI Insights: {db.get('insight_count', 0)}")
        logger.info(f"  Processed: {db.get('processed_percentage', 0)}%")

        # NewsData API
        newsdata = health.get("newsdata_api", {})
        logger.info("\nNewsData.io API:")
        logger.info(f"  Status: {newsdata.get('status', 'unknown')}")

        # API Keys
        keys = health.get("api_keys", {})
        logger.info("\nAPI Keys:")
        for key, configured in keys.items():
            status = "✓" if configured else "✗"
            logger.info(f"  {key}: {status}")

        # Warnings
        warnings = health.get("warnings", [])
        if warnings:
            logger.info("\nWarnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")

        logger.info("=" * 80)


# Convenience function
async def get_health_status() -> Dict[str, Any]:
    """Get current system health status."""
    return await HealthMonitor.full_health_check()
