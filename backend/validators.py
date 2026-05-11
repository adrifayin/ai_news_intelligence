"""
Data Validation and Sanitization
Robust validation for incoming data
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from backend.exceptions import ValidationException
from backend.logger import get_logger

logger = get_logger(__name__)


class ArticleValidator:
    """Validate and sanitize article data."""

    # Validation patterns
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    SPAM_PATTERNS = [
        r'\[removed\]',
        r'\[deleted\]',
        r'click here',
        r'buy now',
        r'limited time',
        r'act now',
    ]

    # Minimum lengths
    MIN_TITLE_LENGTH = 10
    MIN_DESCRIPTION_LENGTH = 20
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 2000
    MAX_CONTENT_LENGTH = 10000

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format."""
        if not url or not isinstance(url, str):
            return False

        if not cls.URL_PATTERN.match(url):
            return False

        # Additional checks
        try:
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https']:
                return False
            if not parsed.netloc:
                return False
            return True
        except Exception:
            return False

    @classmethod
    def validate_title(cls, title: str) -> bool:
        """Validate article title."""
        if not title or not isinstance(title, str):
            return False

        title = title.strip()

        # Check length
        if len(title) < cls.MIN_TITLE_LENGTH:
            return False

        # Check for spam patterns
        title_lower = title.lower()
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, title_lower):
                return False

        return True

    @classmethod
    def sanitize_text(cls, text: Optional[str], max_length: int = None) -> Optional[str]:
        """Sanitize text content."""
        if not text:
            return None

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text.strip() or None

    @classmethod
    def parse_datetime(cls, date_str: str) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
        ]

        # Try ISO format first
        try:
            # Remove timezone info
            date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str.split("+")[0].split("-")[0])
        except Exception:
            pass

        # Try other formats
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except Exception:
                continue

        # Fallback to current time
        logger.warning(f"Could not parse datetime: {date_str}")
        return datetime.utcnow()

    @classmethod
    def validate_article(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean article data.

        Args:
            data: Raw article data

        Returns:
            Cleaned article data

        Raises:
            ValidationException: If validation fails
        """
        errors = []

        # Required fields
        title = data.get("title")
        url = data.get("url") or data.get("link")

        if not title:
            errors.append("Missing title")
        elif not cls.validate_title(title):
            errors.append(f"Invalid title: {title[:50]}")

        if not url:
            errors.append("Missing URL")
        elif not cls.validate_url(url):
            errors.append(f"Invalid URL: {url[:50]}")

        if errors:
            raise ValidationException(f"Article validation failed: {'; '.join(errors)}")

        # Build cleaned article
        cleaned = {
            "title": cls.sanitize_text(title, cls.MAX_TITLE_LENGTH),
            "url": url,
            "description": cls.sanitize_text(
                data.get("description"),
                cls.MAX_DESCRIPTION_LENGTH
            ),
            "content": cls.sanitize_text(
                data.get("content"),
                cls.MAX_CONTENT_LENGTH
            ),
            "source_id": data.get("source_id", ""),
            "source_name": data.get("source_name") or data.get("source_id", "Unknown"),
            "image_url": data.get("image_url"),
            "published_at": cls.parse_datetime(data.get("pubDate") or data.get("published_at", "")),
        }

        # Handle author field
        author = data.get("author") or data.get("creator")
        if isinstance(author, list):
            cleaned["author"] = ", ".join(author[:3]) or None  # Max 3 authors
        else:
            cleaned["author"] = cls.sanitize_text(str(author)) if author else None

        # Handle category
        category = data.get("category", [])
        if isinstance(category, list) and category:
            cleaned["category"] = category[0].lower()
        elif isinstance(category, str):
            cleaned["category"] = category.lower()
        else:
            cleaned["category"] = data.get("_category", "general").lower()

        # Handle country
        country = data.get("country", [])
        if isinstance(country, list) and country:
            cleaned["country"] = country[0].upper()
        elif isinstance(country, str):
            cleaned["country"] = country.upper()
        else:
            cleaned["country"] = None

        # Language
        cleaned["language"] = data.get("language", "en")

        return cleaned


class SentimentValidator:
    """Validate sentiment data."""

    VALID_SENTIMENTS = {"positive", "negative", "neutral"}

    @classmethod
    def validate_sentiment(cls, sentiment: str) -> str:
        """Validate and normalize sentiment."""
        sentiment = str(sentiment).strip().lower()

        if sentiment in cls.VALID_SENTIMENTS:
            return sentiment

        # Try to infer from common variations
        if sentiment in ["pos", "good", "optimistic", "bullish"]:
            return "positive"
        if sentiment in ["neg", "bad", "pessimistic", "bearish"]:
            return "negative"

        return "neutral"

    @classmethod
    def validate_score(cls, score: float) -> float:
        """Validate sentiment score (0.0 to 1.0)."""
        try:
            score = float(score)
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5
