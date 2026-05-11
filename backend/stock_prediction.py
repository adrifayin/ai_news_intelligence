"""
Stock Market Prediction Based on News Sentiment
Uses sentiment signals, market indicators, and time-series forecasting
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class StockPredictor:
    """Predict stock movements based on news sentiment and market data."""

    def __init__(self):
        self.prediction_confidence_threshold = 0.6
        self.sentiment_weight = 0.7
        self.technical_weight = 0.3

    def predict_movement(
        self,
        ticker: str,
        db,
        days_forward: int = 1
    ) -> Dict:
        """
        Predict stock movement based on news sentiment.

        Args:
            ticker: Stock ticker symbol
            db: Database session
            days_forward: How many days to predict (1-7)

        Returns:
            {
                'ticker': str,
                'prediction': 'up' | 'down' | 'neutral',
                'confidence': 0.0-1.0,
                'predicted_change': float (percentage),
                'sentiment_signal': float,
                'momentum': float,
                'risk_level': 'low' | 'medium' | 'high',
                'timeframe': str,
                'recommendation': str
            }
        """
        from backend.database import TickerSentiment, AIInsight, Article

        # Get sentiment data for ticker
        cutoff_date = date.today() - timedelta(days=7)
        sentiment_records = db.query(TickerSentiment).filter(
            TickerSentiment.ticker == ticker,
            TickerSentiment.date >= cutoff_date
        ).order_by(TickerSentiment.date.desc()).all()

        if not sentiment_records:
            return self._no_data_prediction(ticker)

        # Calculate sentiment signal
        sentiment_signal = self._calculate_sentiment_signal(sentiment_records)

        # Calculate momentum
        momentum = self._calculate_momentum(sentiment_records)

        # Get news volume (high volume = higher confidence)
        news_volume = sum(s.mention_count for s in sentiment_records)

        # Calculate sentiment volatility (risk indicator)
        sentiment_volatility = self._calculate_volatility(sentiment_records)

        # Make prediction
        prediction, confidence = self._make_prediction(
            sentiment_signal,
            momentum,
            news_volume,
            sentiment_volatility
        )

        # Estimate price change
        predicted_change = self._estimate_price_change(
            sentiment_signal,
            momentum,
            days_forward
        )

        # Risk assessment
        risk_level = self._assess_risk(sentiment_volatility, confidence, news_volume)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            prediction,
            confidence,
            risk_level,
            sentiment_signal
        )

        return {
            'ticker': ticker,
            'prediction': prediction,
            'confidence': round(confidence, 3),
            'predicted_change': round(predicted_change, 2),
            'sentiment_signal': round(sentiment_signal, 3),
            'momentum': round(momentum, 3),
            'risk_level': risk_level,
            'timeframe': f'{days_forward}d',
            'recommendation': recommendation,
            'data_points': len(sentiment_records),
            'news_volume': news_volume,
            'sentiment_volatility': round(sentiment_volatility, 3)
        }

    def batch_predict(self, tickers: List[str], db) -> List[Dict]:
        """Predict movements for multiple stocks."""
        predictions = []

        for ticker in tickers:
            try:
                pred = self.predict_movement(ticker, db)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Prediction failed for {ticker}: {e}")
                continue

        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return predictions

    def get_top_opportunities(self, db, limit: int = 10) -> Dict:
        """
        Find stocks with highest upside potential based on sentiment.

        Returns top stocks to watch.
        """
        from backend.database import TickerSentiment

        # Get all tickers with recent activity
        cutoff = date.today() - timedelta(days=3)
        recent_tickers = db.query(TickerSentiment.ticker).filter(
            TickerSentiment.date >= cutoff
        ).distinct().all()

        tickers = [t[0] for t in recent_tickers]

        # Predict for all
        predictions = self.batch_predict(tickers, db)

        # Filter for high-confidence bullish predictions
        opportunities = [
            p for p in predictions
            if p['prediction'] == 'up' and p['confidence'] >= 0.6
        ]

        # Also find bearish opportunities (for shorting)
        risks = [
            p for p in predictions
            if p['prediction'] == 'down' and p['confidence'] >= 0.6
        ]

        return {
            'bullish_opportunities': opportunities[:limit],
            'bearish_risks': risks[:limit],
            'total_analyzed': len(predictions),
            'generated_at': datetime.now().isoformat()
        }

    def _calculate_sentiment_signal(self, records: List) -> float:
        """Calculate weighted sentiment signal (more weight to recent)."""
        if not records:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for i, record in enumerate(records):
            # Exponential decay: most recent = highest weight
            weight = (0.8 ** i) * record.mention_count
            weighted_sum += record.avg_sentiment * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _calculate_momentum(self, records: List) -> float:
        """Calculate sentiment momentum (rate of change)."""
        if len(records) < 2:
            return 0.0

        # Compare most recent to average of older data
        recent = records[0].avg_sentiment
        older_avg = sum(r.avg_sentiment for r in records[1:]) / len(records[1:])

        return recent - older_avg

    def _calculate_volatility(self, records: List) -> float:
        """Calculate sentiment volatility (standard deviation)."""
        if len(records) < 2:
            return 0.0

        sentiments = [r.avg_sentiment for r in records]
        mean = sum(sentiments) / len(sentiments)

        variance = sum((s - mean) ** 2 for s in sentiments) / len(sentiments)
        volatility = variance ** 0.5

        return volatility

    def _make_prediction(
        self,
        sentiment: float,
        momentum: float,
        volume: int,
        volatility: float
    ) -> Tuple[str, float]:
        """Make prediction and calculate confidence."""

        # Base prediction on sentiment + momentum
        combined_signal = sentiment + (momentum * 0.5)

        if combined_signal > 0.2:
            prediction = 'up'
            base_confidence = min(abs(combined_signal), 1.0)
        elif combined_signal < -0.2:
            prediction = 'down'
            base_confidence = min(abs(combined_signal), 1.0)
        else:
            prediction = 'neutral'
            base_confidence = 0.5

        # Adjust confidence based on volume (more news = higher confidence)
        if volume > 20:
            volume_boost = 0.2
        elif volume > 10:
            volume_boost = 0.1
        else:
            volume_boost = 0.0

        # Reduce confidence if high volatility (mixed signals)
        if volatility > 0.5:
            volatility_penalty = 0.2
        elif volatility > 0.3:
            volatility_penalty = 0.1
        else:
            volatility_penalty = 0.0

        final_confidence = base_confidence + volume_boost - volatility_penalty
        final_confidence = max(0.1, min(final_confidence, 0.95))

        return prediction, final_confidence

    def _estimate_price_change(
        self,
        sentiment: float,
        momentum: float,
        days: int
    ) -> float:
        """
        Estimate percentage price change.

        This is a simplified model - real prediction would use ML.
        """
        # Base change per day based on sentiment
        daily_change = sentiment * 2.0  # Scale: -1 to 1 sentiment → -2% to 2%

        # Add momentum effect
        momentum_effect = momentum * 1.5

        # Total prediction
        total_change = (daily_change + momentum_effect) * days

        # Clamp to reasonable range (-10% to 10% per prediction)
        return max(-10.0, min(total_change, 10.0))

    def _assess_risk(self, volatility: float, confidence: float, volume: int) -> str:
        """Assess risk level of prediction."""

        risk_score = 0

        # High volatility = higher risk
        if volatility > 0.5:
            risk_score += 2
        elif volatility > 0.3:
            risk_score += 1

        # Low confidence = higher risk
        if confidence < 0.5:
            risk_score += 2
        elif confidence < 0.7:
            risk_score += 1

        # Low volume = higher risk (less data)
        if volume < 5:
            risk_score += 2
        elif volume < 10:
            risk_score += 1

        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        return 'low'

    def _generate_recommendation(
        self,
        prediction: str,
        confidence: float,
        risk_level: str,
        sentiment: float
    ) -> str:
        """Generate actionable recommendation."""

        if risk_level == 'high':
            return "⚠️ High risk - wait for clearer signals before trading"

        if prediction == 'up':
            if confidence >= 0.8:
                return "🟢 Strong buy signal - consider taking position"
            elif confidence >= 0.6:
                return "🟢 Moderate buy - enter with caution"
            else:
                return "🟡 Weak buy signal - monitor closely"

        elif prediction == 'down':
            if confidence >= 0.8:
                return "🔴 Strong sell signal - consider exiting positions"
            elif confidence >= 0.6:
                return "🔴 Moderate sell - reduce exposure"
            else:
                return "🟡 Weak sell signal - hold and monitor"

        else:
            return "⚪ Neutral - no clear direction, hold current positions"

    def _no_data_prediction(self, ticker: str) -> Dict:
        """Return neutral prediction when no data available."""
        return {
            'ticker': ticker,
            'prediction': 'neutral',
            'confidence': 0.0,
            'predicted_change': 0.0,
            'sentiment_signal': 0.0,
            'momentum': 0.0,
            'risk_level': 'high',
            'timeframe': '1d',
            'recommendation': '⚠️ Insufficient data for prediction',
            'data_points': 0,
            'news_volume': 0,
            'sentiment_volatility': 0.0
        }


# ═══════════════════════════════════════════
# Stock Watchlist & Follow Feature
# ═══════════════════════════════════════════

class StockWatchlist:
    """Manage user stock watchlists and alerts."""

    def add_to_watchlist(self, user_id: str, ticker: str, db) -> Dict:
        """Add stock to user's watchlist."""
        from backend.database import text

        # Check if already exists
        result = db.execute(
            text("SELECT * FROM user_watchlist WHERE user_id = :uid AND ticker = :tkr"),
            {"uid": user_id, "tkr": ticker}
        ).first()

        if result:
            return {'status': 'exists', 'message': f'{ticker} already in watchlist'}

        # Add to watchlist
        db.execute(
            text("""
                INSERT INTO user_watchlist (user_id, ticker, added_at)
                VALUES (:uid, :tkr, datetime('now'))
            """),
            {"uid": user_id, "tkr": ticker}
        )
        db.commit()

        return {'status': 'added', 'ticker': ticker}

    def remove_from_watchlist(self, user_id: str, ticker: str, db) -> Dict:
        """Remove stock from watchlist."""
        from backend.database import text

        db.execute(
            text("DELETE FROM user_watchlist WHERE user_id = :uid AND ticker = :tkr"),
            {"uid": user_id, "tkr": ticker}
        )
        db.commit()

        return {'status': 'removed', 'ticker': ticker}

    def get_watchlist(self, user_id: str, db) -> List[Dict]:
        """Get user's watchlist with predictions."""
        from backend.database import text

        result = db.execute(
            text("SELECT ticker, added_at FROM user_watchlist WHERE user_id = :uid ORDER BY added_at DESC"),
            {"uid": user_id}
        ).fetchall()

        if not result:
            return []

        # Get predictions for each ticker
        predictor = StockPredictor()
        watchlist = []

        for row in result:
            ticker = row[0]
            added_at = row[1]

            try:
                prediction = predictor.predict_movement(ticker, db)
                watchlist.append({
                    'ticker': ticker,
                    'added_at': added_at,
                    'prediction': prediction
                })
            except Exception as e:
                logger.warning(f"Failed to predict {ticker}: {e}")

        return watchlist

    def get_alerts(self, user_id: str, db) -> List[Dict]:
        """Get alerts for stocks in watchlist with significant movements."""
        watchlist = self.get_watchlist(user_id, db)

        alerts = []

        for item in watchlist:
            prediction = item['prediction']

            # Alert if high confidence prediction
            if prediction['confidence'] >= 0.7:
                alert_type = 'opportunity' if prediction['prediction'] == 'up' else 'warning'

                alerts.append({
                    'ticker': prediction['ticker'],
                    'type': alert_type,
                    'message': prediction['recommendation'],
                    'confidence': prediction['confidence'],
                    'predicted_change': prediction['predicted_change']
                })

        return alerts
