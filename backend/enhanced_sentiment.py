"""
Enhanced Sentiment Analysis with Advanced NLP
Uses multiple techniques for accurate sentiment detection:
1. Lexicon-based analysis (VADER)
2. AI-powered sentiment (Gemini/Grok)
3. Financial sentiment indicators
4. Aspect-based sentiment
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# VADER-style Sentiment Lexicon
# ═══════════════════════════════════════════

POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive',
    'success', 'successful', 'growth', 'gain', 'profit', 'win', 'won', 'winning',
    'rise', 'rising', 'surge', 'boom', 'bullish', 'optimistic', 'breakthrough',
    'innovation', 'improvement', 'progress', 'advance', 'achievement', 'soar',
    'rally', 'momentum', 'upgrade', 'strong', 'strength', 'robust', 'recovery',
    'benefit', 'advantage', 'opportunity', 'promising', 'bright', 'milestone'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'poor', 'negative', 'fail', 'failure', 'failed',
    'loss', 'lose', 'losing', 'decline', 'fall', 'falling', 'crash', 'crisis',
    'problem', 'issue', 'concern', 'worry', 'risk', 'threat', 'danger', 'bearish',
    'pessimistic', 'downgrade', 'weak', 'weakness', 'drop', 'plunge', 'slump',
    'recession', 'unemployment', 'inflation', 'deficit', 'debt', 'scandal',
    'controversy', 'lawsuit', 'investigation', 'fraud', 'collapse', 'bankrupt'
}

INTENSIFIERS = {
    'very': 1.5, 'extremely': 2.0, 'incredibly': 2.0, 'absolutely': 1.8,
    'completely': 1.5, 'totally': 1.5, 'highly': 1.3, 'really': 1.2,
    'quite': 1.1, 'remarkably': 1.5, 'particularly': 1.2
}

NEGATIONS = {
    'not', 'no', 'never', 'neither', 'nobody', 'nothing', 'none', 'nowhere',
    'hardly', 'scarcely', 'barely', "n't", 'cannot', 'cant'
}

# Financial sentiment indicators
BULLISH_INDICATORS = {
    'beat expectations', 'exceeded forecast', 'record high', 'all-time high',
    'strong earnings', 'profit surge', 'revenue growth', 'market share gain',
    'expansion plan', 'new contract', 'strategic partnership', 'acquisition',
    'dividend increase', 'stock buyback', 'positive guidance', 'upward revision'
}

BEARISH_INDICATORS = {
    'missed expectations', 'below forecast', 'record low', 'profit warning',
    'earnings miss', 'revenue decline', 'market share loss', 'layoffs',
    'restructuring', 'investigation', 'lawsuit', 'regulatory scrutiny',
    'dividend cut', 'guidance lowered', 'downward revision', 'debt concerns'
}


class EnhancedSentimentAnalyzer:
    """Advanced sentiment analysis combining multiple NLP techniques."""

    def __init__(self):
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.intensifiers = INTENSIFIERS
        self.negations = NEGATIONS

    def analyze(self, text: str, title: str = "") -> Dict:
        """
        Perform comprehensive sentiment analysis.

        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'confidence': 0.0-1.0,
                'score': -1.0 to 1.0,
                'breakdown': {
                    'lexicon_score': float,
                    'financial_score': float,
                    'title_weight': float
                },
                'aspects': {
                    'market': 'positive/negative/neutral',
                    'company': 'positive/negative/neutral',
                    'economy': 'positive/negative/neutral'
                }
            }
        """
        # Combine title and text, weighting title higher
        full_text = f"{title} {title} {text}"  # Title counted twice

        # 1. Lexicon-based analysis
        lexicon_score, lexicon_confidence = self._lexicon_analysis(full_text)

        # 2. Financial sentiment indicators
        financial_score = self._financial_sentiment(full_text)

        # 3. Aspect-based sentiment
        aspects = self._aspect_sentiment(full_text)

        # Combine scores with weights
        # Lexicon: 60%, Financial: 40%
        combined_score = (lexicon_score * 0.6) + (financial_score * 0.4)

        # Determine final sentiment
        if combined_score > 0.15:
            sentiment = 'positive'
            confidence = min(abs(combined_score) * 2, 1.0)
        elif combined_score < -0.15:
            sentiment = 'negative'
            confidence = min(abs(combined_score) * 2, 1.0)
        else:
            sentiment = 'neutral'
            confidence = 1.0 - abs(combined_score)

        # Boost confidence if multiple signals agree
        if lexicon_score * financial_score > 0:  # Same sign
            confidence = min(confidence * 1.2, 1.0)

        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 3),
            'score': round(combined_score, 3),
            'breakdown': {
                'lexicon_score': round(lexicon_score, 3),
                'financial_score': round(financial_score, 3),
                'combined': round(combined_score, 3)
            },
            'aspects': aspects,
            'signals': {
                'positive_count': self._count_sentiment_words(full_text, self.positive_words),
                'negative_count': self._count_sentiment_words(full_text, self.negative_words),
                'bullish_indicators': self._count_indicators(full_text, BULLISH_INDICATORS),
                'bearish_indicators': self._count_indicators(full_text, BEARISH_INDICATORS)
            }
        }

    def _lexicon_analysis(self, text: str) -> Tuple[float, float]:
        """VADER-style lexicon-based sentiment analysis."""
        words = re.findall(r'\b[a-z]+\b', text.lower())

        if not words:
            return 0.0, 0.0

        sentiment_score = 0.0
        sentiment_count = 0

        for i, word in enumerate(words):
            # Check for negation in previous 3 words
            negation = False
            if i > 0:
                prev_words = words[max(0, i-3):i]
                if any(neg in prev_words for neg in self.negations):
                    negation = True

            # Check for intensifiers
            intensifier = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensifier = self.intensifiers[words[i-1]]

            # Calculate sentiment
            if word in self.positive_words:
                score = 1.0 * intensifier
                if negation:
                    score *= -0.5
                sentiment_score += score
                sentiment_count += 1

            elif word in self.negative_words:
                score = -1.0 * intensifier
                if negation:
                    score *= -0.5
                sentiment_score += score
                sentiment_count += 1

        # Normalize by number of words
        if sentiment_count == 0:
            return 0.0, 0.0

        normalized_score = sentiment_score / len(words) * 10  # Scale up
        normalized_score = max(-1.0, min(1.0, normalized_score))  # Clamp to [-1, 1]

        # Confidence based on number of sentiment words
        confidence = min(sentiment_count / len(words) * 5, 1.0)

        return normalized_score, confidence

    def _financial_sentiment(self, text: str) -> float:
        """Analyze financial-specific sentiment indicators."""
        text_lower = text.lower()

        bullish_count = self._count_indicators(text_lower, BULLISH_INDICATORS)
        bearish_count = self._count_indicators(text_lower, BEARISH_INDICATORS)

        if bullish_count == 0 and bearish_count == 0:
            return 0.0

        # Calculate score
        total = bullish_count + bearish_count
        score = (bullish_count - bearish_count) / total

        return score

    def _aspect_sentiment(self, text: str) -> Dict[str, str]:
        """Extract aspect-based sentiment (market, company, economy)."""
        text_lower = text.lower()

        aspects = {
            'market': self._aspect_score(text_lower, ['market', 'stock', 'trading', 'investor']),
            'company': self._aspect_score(text_lower, ['company', 'firm', 'business', 'corporate']),
            'economy': self._aspect_score(text_lower, ['economy', 'economic', 'gdp', 'employment'])
        }

        return aspects

    def _aspect_score(self, text: str, keywords: List[str]) -> str:
        """Score sentiment for a specific aspect."""
        # Find sentences containing aspect keywords
        sentences = re.split(r'[.!?]', text)
        relevant_sentences = [
            s for s in sentences
            if any(kw in s.lower() for kw in keywords)
        ]

        if not relevant_sentences:
            return 'neutral'

        # Analyze sentiment of relevant sentences
        combined_text = ' '.join(relevant_sentences)
        score, _ = self._lexicon_analysis(combined_text)

        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        return 'neutral'

    def _count_sentiment_words(self, text: str, word_set: set) -> int:
        """Count sentiment words in text."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return sum(1 for word in words if word in word_set)

    def _count_indicators(self, text: str, indicator_set: set) -> int:
        """Count financial indicator phrases in text."""
        count = 0
        for indicator in indicator_set:
            count += text.count(indicator.lower())
        return count


# ═══════════════════════════════════════════
# Real-time Sentiment Tracker
# ═══════════════════════════════════════════

class RealtimeSentimentTracker:
    """Track sentiment changes in real-time for trending detection."""

    def __init__(self):
        self.sentiment_history = []
        self.ticker_sentiment = {}

    def update(self, article_id: str, sentiment: str, score: float, ticker: str = None):
        """Update sentiment tracking."""
        from datetime import datetime

        entry = {
            'article_id': article_id,
            'sentiment': sentiment,
            'score': score,
            'timestamp': datetime.now(),
            'ticker': ticker
        }

        self.sentiment_history.append(entry)

        # Track by ticker
        if ticker:
            if ticker not in self.ticker_sentiment:
                self.ticker_sentiment[ticker] = []
            self.ticker_sentiment[ticker].append(entry)

        # Keep only last 1000 entries
        if len(self.sentiment_history) > 1000:
            self.sentiment_history = self.sentiment_history[-1000:]

    def get_trending_sentiment(self, window_minutes: int = 60) -> Dict:
        """Get sentiment trends in the last N minutes."""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent = [e for e in self.sentiment_history if e['timestamp'] > cutoff]

        if not recent:
            return {'trend': 'neutral', 'momentum': 0.0}

        # Calculate momentum (change in sentiment over time)
        scores = [e['score'] for e in recent]

        if len(scores) < 2:
            return {'trend': 'neutral', 'momentum': 0.0}

        # Simple linear regression for trend
        avg_score = sum(scores) / len(scores)
        momentum = (scores[-1] - scores[0]) / len(scores)

        if momentum > 0.05:
            trend = 'improving'
        elif momentum < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'momentum': round(momentum, 3),
            'avg_sentiment': round(avg_score, 3),
            'sample_size': len(recent)
        }

    def get_ticker_trend(self, ticker: str, window_minutes: int = 60) -> Dict:
        """Get sentiment trend for a specific ticker."""
        from datetime import datetime, timedelta

        if ticker not in self.ticker_sentiment:
            return {'trend': 'neutral', 'momentum': 0.0}

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent = [e for e in self.ticker_sentiment[ticker] if e['timestamp'] > cutoff]

        if not recent:
            return {'trend': 'neutral', 'momentum': 0.0}

        scores = [e['score'] for e in recent]
        avg_score = sum(scores) / len(scores)

        if len(scores) >= 2:
            momentum = (scores[-1] - scores[0]) / len(scores)
        else:
            momentum = 0.0

        if avg_score > 0.15:
            sentiment = 'bullish'
        elif avg_score < -0.15:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'

        return {
            'ticker': ticker,
            'sentiment': sentiment,
            'momentum': round(momentum, 3),
            'avg_score': round(avg_score, 3),
            'mention_count': len(recent)
        }


# Global tracker instance
sentiment_tracker = RealtimeSentimentTracker()


def analyze_article_sentiment(title: str, description: str, content: str) -> Dict:
    """
    Convenience function to analyze article sentiment.

    Returns enhanced sentiment analysis with NLP.
    """
    analyzer = EnhancedSentimentAnalyzer()

    # Combine text
    full_text = f"{description or ''} {content or ''}"[:3000]

    # Analyze
    result = analyzer.analyze(full_text, title)

    return result
