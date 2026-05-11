"""
Advanced Algorithms for News Intelligence Platform
Includes:
1. Personalized News Recommendation (Collaborative + Content-based)
2. Advanced Article Clustering (TF-IDF + K-means + Topic Modeling)
3. Trend Detection & Forecasting (Time-series analysis)
"""

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import math

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# 1. PERSONALIZED NEWS RECOMMENDATION ENGINE
# ═══════════════════════════════════════════

class NewsRecommender:
    """Hybrid recommendation system combining collaborative and content-based filtering."""

    def __init__(self):
        self.user_item_matrix = {}
        self.article_features = {}
        self.user_profiles = {}

    def build_user_item_matrix(self, db) -> Dict:
        """Build user-article interaction matrix from database."""
        from backend.database import UserArticleInteraction, User

        interactions = db.query(UserArticleInteraction).all()

        # Weight different interaction types
        interaction_weights = {
            'read': 1.0,
            'like': 3.0,
            'bookmark': 2.5,
            'dismiss': -1.0,
            'dislike': -2.0,
        }

        matrix = defaultdict(lambda: defaultdict(float))

        for interaction in interactions:
            weight = interaction_weights.get(interaction.interaction_type, 0.0)
            matrix[interaction.user_id][interaction.article_id] += weight

        self.user_item_matrix = dict(matrix)
        return self.user_item_matrix

    def extract_article_features(self, articles: List[Dict]) -> np.ndarray:
        """Extract TF-IDF features from articles for content-based filtering."""
        texts = []
        article_ids = []

        for article in articles:
            # Combine title, description, and category for feature extraction
            text = f"{article.get('title', '')} {article.get('description', '')} {article.get('category', '')}"
            texts.append(text)
            article_ids.append(article['id'])

        if not texts:
            return np.array([]), []

        vectorizer = TfidfVectorizer(max_features=200, stop_words='english')
        feature_matrix = vectorizer.fit_transform(texts)

        # Store features for each article
        for i, article_id in enumerate(article_ids):
            self.article_features[article_id] = feature_matrix[i]

        return feature_matrix, article_ids

    def collaborative_filtering_score(self, user_id: str, article_id: str, db) -> float:
        """Calculate recommendation score using user-user collaborative filtering."""
        if user_id not in self.user_item_matrix:
            return 0.0

        target_user_ratings = self.user_item_matrix[user_id]

        # Find similar users who interacted with this article
        similar_users_scores = []

        for other_user_id, other_ratings in self.user_item_matrix.items():
            if other_user_id == user_id:
                continue

            if article_id not in other_ratings:
                continue

            # Calculate user similarity using Pearson correlation
            common_articles = set(target_user_ratings.keys()) & set(other_ratings.keys())

            if len(common_articles) < 2:
                continue

            # Compute similarity
            target_vec = [target_user_ratings[aid] for aid in common_articles]
            other_vec = [other_ratings[aid] for aid in common_articles]

            similarity = self._pearson_correlation(target_vec, other_vec)

            if similarity > 0:
                similar_users_scores.append(similarity * other_ratings[article_id])

        if not similar_users_scores:
            return 0.0

        return np.mean(similar_users_scores)

    def content_based_score(self, user_id: str, article_id: str, articles: List[Dict]) -> float:
        """Calculate recommendation score based on content similarity to user's history."""
        if user_id not in self.user_item_matrix:
            return 0.0

        user_interactions = self.user_item_matrix[user_id]

        if article_id not in self.article_features:
            return 0.0

        # Get articles user liked
        liked_articles = [aid for aid, score in user_interactions.items() if score > 0]

        if not liked_articles:
            return 0.0

        # Calculate similarity to articles user liked
        target_features = self.article_features[article_id]
        similarities = []

        for liked_id in liked_articles:
            if liked_id in self.article_features:
                liked_features = self.article_features[liked_id]
                sim = cosine_similarity(target_features, liked_features)[0][0]
                similarities.append(sim * user_interactions[liked_id])

        if not similarities:
            return 0.0

        return np.mean(similarities)

    def recommend(self, user_id: str, articles: List[Dict], db, top_k: int = 20) -> List[Dict]:
        """Generate personalized recommendations using hybrid approach."""

        # Build matrices
        self.build_user_item_matrix(db)
        self.extract_article_features(articles)

        # Score each article
        scored_articles = []

        for article in articles:
            article_id = article['id']

            # Skip articles user already interacted with
            if user_id in self.user_item_matrix and article_id in self.user_item_matrix[user_id]:
                continue

            # Hybrid score: 60% collaborative, 40% content-based
            collab_score = self.collaborative_filtering_score(user_id, article_id, db)
            content_score = self.content_based_score(user_id, article_id, articles)

            hybrid_score = 0.6 * collab_score + 0.4 * content_score

            # Boost recent articles
            published_at = article.get('published_at')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    hours_old = (datetime.now() - pub_date.replace(tzinfo=None)).total_seconds() / 3600
                    recency_boost = max(0, 1.0 - (hours_old / 72))  # Decay over 3 days
                    hybrid_score += recency_boost * 0.2
                except:
                    pass

            scored_articles.append({
                **article,
                'recommendation_score': hybrid_score,
                'collab_score': collab_score,
                'content_score': content_score,
            })

        # Sort by score
        scored_articles.sort(key=lambda x: x['recommendation_score'], reverse=True)

        return scored_articles[:top_k]

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n == 0:
            return 0.0

        sum_x = sum(x)
        sum_y = sum(y)
        sum_x_sq = sum(xi**2 for xi in x)
        sum_y_sq = sum(yi**2 for yi in y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x_sq - sum_x**2) * (n * sum_y_sq - sum_y**2))

        if denominator == 0:
            return 0.0

        return numerator / denominator


# ═══════════════════════════════════════════
# 2. ADVANCED ARTICLE CLUSTERING
# ═══════════════════════════════════════════

class AdvancedClusterer:
    """ML-based article clustering using TF-IDF + DBSCAN/K-means."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=300,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )

    def cluster_articles_ml(self, articles: List[Dict], method: str = 'dbscan') -> List[Dict]:
        """
        Cluster articles using machine learning algorithms.

        Args:
            articles: List of article dictionaries
            method: 'dbscan' or 'kmeans'

        Returns:
            List of cluster dictionaries with article IDs and metadata
        """
        if len(articles) < 3:
            return []

        # Prepare text data
        texts = []
        article_data = []

        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            if text.strip():
                texts.append(text)
                article_data.append(article)

        if len(texts) < 3:
            return []

        # Extract TF-IDF features
        try:
            feature_matrix = self.vectorizer.fit_transform(texts)
        except Exception as e:
            logger.warning(f"TF-IDF extraction failed: {e}")
            return []

        # Perform clustering
        if method == 'dbscan':
            clusters = self._dbscan_clustering(feature_matrix, article_data)
        else:
            clusters = self._kmeans_clustering(feature_matrix, article_data)

        return clusters

    def _dbscan_clustering(self, feature_matrix, articles: List[Dict]) -> List[Dict]:
        """DBSCAN clustering - automatically finds number of clusters."""
        # Convert to dense for cosine distance
        distance_matrix = 1 - cosine_similarity(feature_matrix)

        # DBSCAN with cosine distance
        clustering = DBSCAN(eps=0.4, min_samples=2, metric='precomputed')
        labels = clustering.fit_predict(distance_matrix)

        return self._format_clusters(labels, articles)

    def _kmeans_clustering(self, feature_matrix, articles: List[Dict]) -> List[Dict]:
        """K-means clustering - fixed number of clusters."""
        # Determine optimal k using elbow method (simplified)
        n_articles = len(articles)
        k = min(max(3, n_articles // 10), 15)  # Between 3 and 15 clusters

        clustering = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = clustering.fit_predict(feature_matrix)

        return self._format_clusters(labels, articles)

    def _format_clusters(self, labels, articles: List[Dict]) -> List[Dict]:
        """Format clustering results into structured output."""
        cluster_map = defaultdict(list)

        for label, article in zip(labels, articles):
            if label != -1:  # Skip noise points in DBSCAN
                cluster_map[label].append(article)

        clusters = []
        for cluster_id, cluster_articles in cluster_map.items():
            if len(cluster_articles) < 2:
                continue

            # Extract topic from most common words
            all_text = ' '.join([a.get('title', '') for a in cluster_articles])
            topic = self._extract_topic(all_text)

            # Determine if underreported (few sources)
            unique_sources = len(set(a.get('source_name', '') for a in cluster_articles))
            is_underreported = unique_sources <= 2

            clusters.append({
                'topic': topic,
                'article_ids': [a['id'] for a in cluster_articles],
                'article_count': len(cluster_articles),
                'source_count': unique_sources,
                'is_underreported': is_underreported,
                'categories': list(set(a.get('category', 'general') for a in cluster_articles)),
            })

        return clusters

    def topic_modeling(self, articles: List[Dict], n_topics: int = 10) -> List[Dict]:
        """
        Extract latent topics using LDA (Latent Dirichlet Allocation).

        Returns topics with top keywords and associated articles.
        """
        if len(articles) < 10:
            return []

        texts = [f"{a.get('title', '')} {a.get('description', '')}" for a in articles]

        try:
            # TF-IDF vectorization
            feature_matrix = self.vectorizer.fit_transform(texts)

            # LDA topic modeling
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=10
            )
            lda.fit(feature_matrix)

            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()

            topics = []
            for topic_idx, topic in enumerate(lda.components_):
                # Get top 10 words for this topic
                top_indices = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_indices]

                # Find articles most associated with this topic
                doc_topic_dist = lda.transform(feature_matrix)
                article_indices = np.where(doc_topic_dist[:, topic_idx] > 0.3)[0]

                if len(article_indices) > 0:
                    topics.append({
                        'topic_id': topic_idx,
                        'keywords': top_words,
                        'article_ids': [articles[i]['id'] for i in article_indices],
                        'article_count': len(article_indices),
                        'topic_strength': float(np.mean(doc_topic_dist[:, topic_idx])),
                    })

            return topics

        except Exception as e:
            logger.warning(f"Topic modeling failed: {e}")
            return []

    @staticmethod
    def _extract_topic(text: str, max_words: int = 4) -> str:
        """Extract topic from text using most frequent meaningful words."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'has', 'have', 'had', 'new', 'says', 'said'
        }

        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(w for w in words if w not in stop_words)

        top_words = [word for word, _ in word_freq.most_common(max_words)]
        return ' '.join(w.capitalize() for w in top_words) or "News Cluster"


# ═══════════════════════════════════════════
# 3. TREND DETECTION & FORECASTING
# ═══════════════════════════════════════════

class TrendDetector:
    """Detect emerging trends and forecast sentiment shifts using time-series analysis."""

    def __init__(self):
        self.trend_threshold = 1.5  # Std deviations above mean for trend detection

    def detect_emerging_trends(self, articles: List[Dict], window_hours: int = 24) -> List[Dict]:
        """
        Detect emerging trends by analyzing keyword frequency over time.

        Args:
            articles: List of articles with timestamps
            window_hours: Time window to analyze (default 24h)

        Returns:
            List of trending topics with metadata
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)

        # Filter recent articles
        recent_articles = []
        for article in articles:
            pub_at = article.get('published_at')
            if pub_at:
                try:
                    pub_date = datetime.fromisoformat(pub_at.replace('Z', '+00:00'))
                    if pub_date.replace(tzinfo=None) > cutoff_time:
                        recent_articles.append({**article, '_pub_date': pub_date.replace(tzinfo=None)})
                except:
                    pass

        if len(recent_articles) < 5:
            return []

        # Split into time buckets (6-hour intervals)
        n_buckets = 4
        bucket_size = window_hours / n_buckets

        buckets = [[] for _ in range(n_buckets)]

        for article in recent_articles:
            hours_ago = (datetime.now() - article['_pub_date']).total_seconds() / 3600
            bucket_idx = min(int(hours_ago / bucket_size), n_buckets - 1)
            buckets[bucket_idx].append(article)

        # Extract keywords from each bucket
        bucket_keywords = []
        for bucket_articles in buckets:
            keywords = self._extract_keywords([a.get('title', '') for a in bucket_articles])
            bucket_keywords.append(keywords)

        # Find keywords with increasing frequency (trending up)
        trends = []

        if len(bucket_keywords) >= 2:
            recent_keywords = bucket_keywords[0]  # Most recent bucket
            older_keywords = Counter()
            for bk in bucket_keywords[1:]:
                older_keywords.update(bk)

            for keyword, recent_count in recent_keywords.items():
                older_count = older_keywords.get(keyword, 0)

                # Calculate growth rate
                if older_count > 0:
                    growth_rate = (recent_count - older_count) / older_count
                else:
                    growth_rate = recent_count  # New keyword

                # Trending if significant growth
                if growth_rate > 0.5 and recent_count >= 2:
                    # Find articles about this trend
                    related_articles = [
                        a for a in recent_articles
                        if keyword.lower() in a.get('title', '').lower()
                    ]

                    trends.append({
                        'keyword': keyword,
                        'recent_mentions': recent_count,
                        'growth_rate': round(growth_rate, 2),
                        'trending_score': recent_count * (1 + growth_rate),
                        'article_ids': [a['id'] for a in related_articles[:5]],
                        'article_count': len(related_articles),
                    })

        # Sort by trending score
        trends.sort(key=lambda x: x['trending_score'], reverse=True)

        return trends[:10]

    def forecast_sentiment(self, db, ticker: str = None, days_back: int = 7) -> Dict:
        """
        Forecast sentiment trends using simple moving average and momentum.

        Args:
            db: Database session
            ticker: Optional stock ticker to analyze
            days_back: Number of days of historical data to use

        Returns:
            Forecast with predicted sentiment direction
        """
        from backend.database import AIInsight, Article, TickerSentiment
        from datetime import date

        # Get historical sentiment data
        if ticker:
            # Ticker-specific sentiment
            cutoff_date = date.today() - timedelta(days=days_back)
            sentiment_records = db.query(TickerSentiment).filter(
                TickerSentiment.ticker == ticker,
                TickerSentiment.date >= cutoff_date
            ).order_by(TickerSentiment.date).all()

            time_series = [
                {
                    'date': str(s.date),
                    'sentiment': s.avg_sentiment,
                    'mentions': s.mention_count
                }
                for s in sentiment_records
            ]
        else:
            # Overall sentiment
            cutoff_time = datetime.now() - timedelta(days=days_back)
            articles = db.query(Article, AIInsight).join(
                AIInsight, Article.id == AIInsight.article_id
            ).filter(Article.published_at >= cutoff_time).all()

            # Group by day
            daily_sentiment = defaultdict(list)
            for article, insight in articles:
                if article.published_at:
                    day = article.published_at.date()
                    sentiment_val = {'positive': 1.0, 'negative': -1.0, 'neutral': 0.0}.get(
                        insight.sentiment, 0.0
                    )
                    daily_sentiment[day].append(sentiment_val)

            time_series = [
                {
                    'date': str(day),
                    'sentiment': np.mean(sentiments),
                    'mentions': len(sentiments)
                }
                for day, sentiments in sorted(daily_sentiment.items())
            ]

        if len(time_series) < 3:
            return {
                'forecast': 'neutral',
                'confidence': 0.0,
                'reason': 'Insufficient historical data'
            }

        # Calculate moving average and momentum
        sentiments = [s['sentiment'] for s in time_series]

        # Simple moving average (last 3 days)
        sma_3 = np.mean(sentiments[-3:])

        # Momentum (rate of change)
        if len(sentiments) >= 2:
            momentum = sentiments[-1] - sentiments[-2]
        else:
            momentum = 0

        # Forecast
        predicted_sentiment = sma_3 + (momentum * 0.5)

        # Classify forecast
        if predicted_sentiment > 0.2:
            forecast = 'bullish'
            confidence = min(abs(predicted_sentiment), 1.0)
        elif predicted_sentiment < -0.2:
            forecast = 'bearish'
            confidence = min(abs(predicted_sentiment), 1.0)
        else:
            forecast = 'neutral'
            confidence = 1.0 - abs(predicted_sentiment)

        return {
            'forecast': forecast,
            'predicted_value': round(predicted_sentiment, 3),
            'confidence': round(confidence, 3),
            'momentum': round(momentum, 3),
            'sma_3': round(sma_3, 3),
            'time_series': time_series,
            'data_points': len(time_series),
        }

    def detect_viral_potential(self, article: Dict, db) -> Dict:
        """
        Predict if an article has potential to go viral based on multiple signals.

        Factors considered:
        - Source reputation
        - Sentiment strength
        - Topic relevance
        - Timing
        """
        score = 0.0
        signals = []

        # 1. Sentiment strength (polarized content spreads faster)
        if article.get('ai'):
            confidence = article['ai'].get('confidence', 0)
            sentiment = article['ai'].get('sentiment', 'neutral')

            if sentiment in ['positive', 'negative'] and confidence > 0.7:
                score += 20
                signals.append(f"Strong {sentiment} sentiment")

        # 2. Recency (fresh content)
        pub_at = article.get('published_at')
        if pub_at:
            try:
                pub_date = datetime.fromisoformat(pub_at.replace('Z', '+00:00'))
                hours_old = (datetime.now() - pub_date.replace(tzinfo=None)).total_seconds() / 3600

                if hours_old < 6:
                    score += 30
                    signals.append("Very recent article")
                elif hours_old < 24:
                    score += 15
                    signals.append("Recent article")
            except:
                pass

        # 3. Controversial topics (keywords that generate engagement)
        controversial_keywords = [
            'scandal', 'crisis', 'controversy', 'protest', 'lawsuit', 'breakthrough',
            'shocking', 'unprecedented', 'record', 'historic', 'banned', 'arrest'
        ]

        title = article.get('title', '').lower()
        matching_keywords = [kw for kw in controversial_keywords if kw in title]

        if matching_keywords:
            score += 15 * len(matching_keywords)
            signals.append(f"Controversial topics: {', '.join(matching_keywords)}")

        # 4. Check if topic is currently trending
        category = article.get('category', '')
        if category:
            # This would be enhanced with real-time trending data
            score += 10
            signals.append(f"Category: {category}")

        # Normalize score to 0-100
        viral_score = min(score, 100)

        # Classification
        if viral_score >= 70:
            prediction = 'high'
        elif viral_score >= 40:
            prediction = 'medium'
        else:
            prediction = 'low'

        return {
            'viral_score': viral_score,
            'prediction': prediction,
            'signals': signals,
            'article_id': article['id'],
        }

    @staticmethod
    def _extract_keywords(texts: List[str]) -> Counter:
        """Extract keywords from a list of texts."""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'has', 'have', 'had', 'new', 'says', 'said', 'will', 'can'
        }

        keywords = Counter()
        for text in texts:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            for word in words:
                if word not in stop_words:
                    keywords[word] += 1

        return keywords


# ═══════════════════════════════════════════
# ALGORITHM ORCHESTRATOR
# ═══════════════════════════════════════════

class AlgorithmOrchestrator:
    """Orchestrates all algorithms and manages their execution."""

    def __init__(self):
        self.recommender = NewsRecommender()
        self.clusterer = AdvancedClusterer()
        self.trend_detector = TrendDetector()

    def run_all_algorithms(self, db) -> Dict:
        """
        Run all algorithms and return comprehensive analysis.

        Returns:
            Dictionary with results from all algorithms
        """
        from backend.database import get_articles

        logger.info("Running algorithm suite...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': {},
            'clusters': [],
            'topics': [],
            'trends': [],
            'forecasts': {},
        }

        # Get articles
        articles_data = get_articles(db, page=1, limit=200)
        articles = articles_data.get('articles', [])

        if not articles:
            logger.warning("No articles available for algorithm processing")
            return results

        # 1. Advanced Clustering
        logger.info("Running ML clustering...")
        clusters = self.clusterer.cluster_articles_ml(articles, method='dbscan')
        results['clusters'] = clusters

        # 2. Topic Modeling
        logger.info("Running topic modeling...")
        topics = self.clusterer.topic_modeling(articles, n_topics=8)
        results['topics'] = topics

        # 3. Trend Detection
        logger.info("Detecting emerging trends...")
        trends = self.trend_detector.detect_emerging_trends(articles, window_hours=48)
        results['trends'] = trends

        # 4. Sentiment Forecasting
        logger.info("Forecasting sentiment...")
        overall_forecast = self.trend_detector.forecast_sentiment(db, days_back=7)
        results['forecasts']['overall'] = overall_forecast

        # 5. Viral Potential
        logger.info("Analyzing viral potential...")
        viral_articles = []
        for article in articles[:50]:  # Check top 50 recent articles
            viral_analysis = self.trend_detector.detect_viral_potential(article, db)
            if viral_analysis['prediction'] in ['high', 'medium']:
                viral_articles.append(viral_analysis)

        results['viral_candidates'] = viral_articles

        logger.info(f"Algorithm suite complete: {len(clusters)} clusters, {len(topics)} topics, {len(trends)} trends")

        return results
