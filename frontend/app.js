/**
 * DataStraw News Intelligence — Frontend Application
 * Vanilla JS: API calls, rendering, interactions, Chart.js
 *
 * FIXES APPLIED:
 * - FIX 1: Sentiment badge colors (green/red/gray)
 * - FIX 2: Infinite scroll with IntersectionObserver
 * - FIX 3: Trending keywords tag cloud (clickable)
 * - FIX 4: Story clusters horizontal cards
 * - FIX 5: Sentiment chart rendering
 * - FIX 6: Markets page with tickers, weather, mood
 * - FIX 7: Predictions page with AI analysis
 */

const API = '';  // Same origin

// ═══════════════════════════════════════════
// State
// ═══════════════════════════════════════════
const state = {
  currentPage: 1,
  currentCategory: 'all',
  currentSentiment: '',
  searchQuery: '',
  totalPages: 1,
  bookmarks: JSON.parse(localStorage.getItem('bookmarks') || '[]'),
  isLoading: false,
  hasMore: true,  // FIX 2: For infinite scroll
};

// ═══════════════════════════════════════════
// API Client with Error Handling
// ═══════════════════════════════════════════
async function fetchAPI(endpoint, options = {}) {
  try {
    const url = new URL(endpoint, window.location.origin);
    if (options.params) {
      Object.entries(options.params).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v);
      });
    }
    const res = await fetch(url, {
      method: options.method || 'GET',
      headers: options.body ? { 'Content-Type': 'application/json' } : {},
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    if (!res.ok) {
      console.error(`API error ${res.status}: ${endpoint}`);
      throw new Error(`API error: ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API call failed: ${endpoint}`, err);
    showError(`Failed to load data: ${err.message}`);
    return null;
  }
}

function showError(message) {
  // Simple error toast
  const toast = document.createElement('div');
  toast.className = 'error-toast';
  toast.textContent = message;
  toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#ef4444;color:white;padding:12px 20px;border-radius:8px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.3)';
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// ═══════════════════════════════════════════
// Theme Toggle
// ═══════════════════════════════════════════
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.textContent = saved === 'dark' ? '🌙' : '☀️';
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      btn.textContent = next === 'dark' ? '🌙' : '☀️';
    });
  }
}

// ═══════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════
function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function countryFlag(code) {
  if (!code || code.length !== 2) return '🌐';
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => 0x1F1E6 + c.charCodeAt(0) - 65));
}

function formatNumber(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toString();
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ═══════════════════════════════════════════
// Page Detection & Init
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initAuth();  // Initialize authentication
  const path = window.location.pathname;
  if (path === '/' || path === '/index.html' || path === '') initNewsDashboard();
  else if (path === '/market' || path === '/market.html') initMarketPage();
  else if (path === '/predictions' || path === '/predictions.html') initPredictionsPage();
});

// ═══════════════════════════════════════════
// PAGE 1: News Dashboard
// ═══════════════════════════════════════════
async function initNewsDashboard() {
  loadStats();
  loadArticles();
  loadClusters();  // FIX 4
  loadTrending();  // FIX 3
  initFilters();
  initSearch();
  initChat();
  initRefresh();
  initInfiniteScroll();  // FIX 2
}

async function loadStats() {
  const data = await fetchAPI('/api/stats');
  if (!data) return;
  setText('statTotal', data.total_articles);
  setText('statPositive', data.sentiment?.positive || 0);
  setText('statNegative', data.sentiment?.negative || 0);
  setText('statNeutral', data.sentiment?.neutral || 0);
  setText('statSources', data.unique_sources || 0);

  // FIX 5: Render sentiment pie chart with correct colors
  const ctx = document.getElementById('sentimentChart');
  if (ctx && data.sentiment) {
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Positive', 'Negative', 'Neutral'],
        datasets: [{
          data: [data.sentiment.positive, data.sentiment.negative, data.sentiment.neutral],
          backgroundColor: ['#16a34a', '#dc2626', '#6b7280'],  // FIX 1: Exact colors
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { color: getCSSVar('--text-secondary'), padding: 12, font: { family: 'Inter' } } }
        }
      }
    });
  }
}

async function loadArticles(append = false) {
  const grid = document.getElementById('articlesGrid');
  if (!grid) return;

  if (!append) {
    grid.innerHTML = '<div class="skeleton skeleton-card"></div>'.repeat(3);
  }

  const data = await fetchAPI('/api/articles', {
    params: {
      category: state.currentCategory !== 'all' ? state.currentCategory : null,
      search: state.searchQuery || null,
      sentiment: state.currentSentiment || null,
      page: state.currentPage,
      limit: 20,
      user_id: authState.user?.id || null,  // Pass user ID for personalized feed
    }
  });

  if (!data || !data.articles?.length) {
    if (!append) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No articles found. Click Refresh to fetch news.</div></div>';
    }
    state.hasMore = false;
    return;
  }

  state.totalPages = data.pages;
  state.hasMore = data.has_more;  // FIX 2

  if (append) {
    grid.insertAdjacentHTML('beforeend', data.articles.map(renderArticleCard).join(''));
  } else {
    grid.innerHTML = data.articles.map(renderArticleCard).join('');
  }

  // Attach event listeners
  grid.querySelectorAll('.insights-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const list = btn.nextElementSibling;
      list.classList.toggle('show');
      btn.textContent = list.classList.contains('show') ? '▲ Hide Insights' : '▼ Show Insights';
    });
  });

  grid.querySelectorAll('.bookmark-btn').forEach(btn => {
    btn.addEventListener('click', () => toggleBookmark(btn.dataset.id, btn));
  });

  // NEW: Attach AI analyze button listeners (on-demand processing only)
  grid.querySelectorAll('.ai-analyze-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const articleId = btn.dataset.id;
      await processArticleOnDemand(articleId, btn);
    });
  });
}

// On-demand AI processing when user clicks the button
async function processArticleOnDemand(articleId, button) {
  const articleCard = button.closest('.article-card');
  const loadingDiv = articleCard.querySelector('.ai-loading');
  const summaryP = articleCard.querySelector('.article-summary');

  // Show loading state
  button.style.display = 'none';
  if (loadingDiv) loadingDiv.style.display = 'block';

  try {
    // Request AI processing
    const result = await fetchAPI(`/api/articles/${articleId}?process=true`);

    if (result && result.ai && result.ai.summary) {
      // Update the card with AI results
      if (summaryP) {
        summaryP.textContent = result.ai.summary;
      }

      // Add insights if available
      const insights = result.ai.insights || [];
      if (insights.length > 0) {
        const insightsHTML = `
          <button class="insights-toggle">▲ Hide Insights</button>
          <ul class="insights-list show">${insights.map(i => `<li>${escHtml(i)}</li>`).join('')}</ul>
        `;

        const sentimentBadgeDiv = articleCard.querySelector('.sentiment-badge').parentElement;
        sentimentBadgeDiv.insertAdjacentHTML('afterend', insightsHTML);

        // Attach toggle listener
        const toggleBtn = articleCard.querySelector('.insights-toggle');
        if (toggleBtn) {
          toggleBtn.addEventListener('click', () => {
            const list = toggleBtn.nextElementSibling;
            list.classList.toggle('show');
            toggleBtn.textContent = list.classList.contains('show') ? '▲ Hide Insights' : '▼ Show Insights';
          });
        }
      }

      // Hide loading
      if (loadingDiv) loadingDiv.style.display = 'none';

      // Show success message briefly
      const successDiv = document.createElement('div');
      successDiv.style.cssText = 'color:#16a34a;font-size:0.85rem;padding:8px;text-align:center;font-weight:600';
      successDiv.textContent = '✓ AI analysis complete!';
      if (loadingDiv) {
        loadingDiv.parentNode.replaceChild(successDiv, loadingDiv);
        setTimeout(() => successDiv.remove(), 3000);
      }

    } else {
      throw new Error('AI processing failed');
    }

  } catch (error) {
    console.error('AI processing error:', error);

    // Show error state
    if (loadingDiv) {
      loadingDiv.innerHTML = '<p style="color:#dc2626;font-size:0.85rem">AI processing failed. Please try again.</p>';
      setTimeout(() => {
        loadingDiv.style.display = 'none';
        button.style.display = 'inline-block';
      }, 3000);
    }
  }
}

function renderArticleCard(article) {
  const ai = article.ai || {};
  const sentimentClass = ai.sentiment || 'neutral';
  const sentimentScore = ai.sentiment_score || ai.confidence || 0;
  const confidence = Math.round(sentimentScore * 100);
  const insights = ai.insights || [];
  const isBookmarked = state.bookmarks.includes(article.id);
  const imgSrc = article.image_url || '';
  const imgHtml = imgSrc
    ? `<img class="article-image" src="${imgSrc}" alt="" loading="lazy" onerror="this.style.display='none'">`
    : '';

  // FIX 1: Sentiment badge with validated colors
  const sentimentBadgeColor = sentimentClass === 'positive' ? '#16a34a' : sentimentClass === 'negative' ? '#dc2626' : '#6b7280';

  // Check if article has AI summary and insights
  const hasAI = ai.summary && ai.summary.length > 0;

  return `
    <article class="article-card" data-article-id="${article.id}">
      ${imgHtml}
      <div class="article-body">
        <div class="article-meta">
          <span class="source-badge">${escHtml(article.source_name || 'Unknown')}</span>
          <span class="country-badge">${countryFlag(article.country)} ${article.country || ''}</span>
          <span class="reading-time">${ai.reading_time || '?'} min read</span>
        </div>
        <h3 class="article-title"><a href="${escHtml(article.url || '#')}" target="_blank" rel="noopener">${escHtml(article.title)}</a></h3>

        ${hasAI ? `
          <p class="article-summary">${escHtml(ai.summary)}</p>
        ` : `
          <p class="article-summary">${escHtml(article.description || '').slice(0, 200)}</p>
          <button class="ai-analyze-btn" data-id="${article.id}" style="background:#2563eb;color:white;border:none;padding:8px 16px;border-radius:6px;font-weight:600;cursor:pointer;margin-top:8px;font-size:0.85rem">
            🤖 Get AI Summary & Insights
          </button>
          <div class="ai-loading" style="display:none;text-align:center;padding:12px;color:var(--text-muted)">
            <div class="spinner" style="border:3px solid var(--text-muted);border-top-color:#2563eb;border-radius:50%;width:24px;height:24px;animation:spin 1s linear infinite;margin:0 auto 8px"></div>
            <p style="font-size:0.85rem">Analyzing article with AI...</p>
          </div>
        `}

        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;margin-top:8px">
          <span class="sentiment-badge" style="background:${sentimentBadgeColor};color:white;padding:4px 10px;border-radius:4px;font-size:0.75rem;font-weight:600">
            ${sentimentIcon(sentimentClass)} ${capitalize(sentimentClass)} ${confidence}%
          </span>
          ${(ai.tickers || []).map(t => `<span class="source-badge" style="font-size:0.7rem">$${escHtml(t)}</span>`).join('')}
        </div>

        ${insights.length ? `
          <button class="insights-toggle">▲ Hide Insights</button>
          <ul class="insights-list show">${insights.map(i => `<li>${escHtml(i)}</li>`).join('')}</ul>
        ` : ''}
      </div>
      <div class="article-footer">
        <span class="coverage-badge">${formatDate(article.published_at)}</span>
        <button class="bookmark-btn ${isBookmarked ? 'bookmarked' : ''}" data-id="${article.id}" title="Bookmark">${isBookmarked ? '★' : '☆'}</button>
      </div>
    </article>`;
}

function sentimentIcon(s) {
  return s === 'positive' ? '↑' : s === 'negative' ? '↓' : '→';
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// FIX 2: Infinite Scroll with IntersectionObserver
function initInfiniteScroll() {
  const sentinel = document.getElementById('scroll-sentinel');
  const loadingSpinner = document.getElementById('loading-spinner');

  if (!sentinel) {
    // Create sentinel and spinner if not exists
    const grid = document.getElementById('articlesGrid');
    if (!grid || !grid.parentElement) return;

    const sentinelDiv = document.createElement('div');
    sentinelDiv.id = 'scroll-sentinel';
    sentinelDiv.style.height = '1px';
    grid.parentElement.appendChild(sentinelDiv);

    const spinnerDiv = document.createElement('div');
    spinnerDiv.id = 'loading-spinner';
    spinnerDiv.className = 'loading-spinner hidden';
    spinnerDiv.innerHTML = '<div class="spinner"></div><p>Loading more articles...</p>';
    grid.parentElement.appendChild(spinnerDiv);
  }

  const observer = new IntersectionObserver(async (entries) => {
    const sentinel = document.getElementById('scroll-sentinel');
    const spinner = document.getElementById('loading-spinner');

    if (entries[0].isIntersecting && !state.isLoading && state.hasMore) {
      state.isLoading = true;
      if (spinner) spinner.classList.remove('hidden');

      state.currentPage++;
      await loadArticles(true);  // Append mode

      if (spinner) spinner.classList.add('hidden');
      state.isLoading = false;

      // Show "No more articles" if done
      if (!state.hasMore && spinner) {
        spinner.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px">No more articles</p>';
        spinner.classList.remove('hidden');
      }
    }
  }, { rootMargin: '200px' });

  const finalSentinel = document.getElementById('scroll-sentinel');
  if (finalSentinel) {
    observer.observe(finalSentinel);
  }
}

// FIX 4: Load Story Clusters
async function loadClusters() {
  const el = document.getElementById('clustersList');
  if (!el) return;
  const data = await fetchAPI('/api/clusters');
  if (!data || !data.length) {
    el.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem">No clusters yet.</p>';
    return;
  }
  el.innerHTML = data.slice(0, 8).map(c => {
    const sentimentColor = c.avg_sentiment === 'positive' ? '#16a34a' : c.avg_sentiment === 'negative' ? '#dc2626' : '#6b7280';
    return `
      <div class="cluster-item" onclick="filterByCluster('${escHtml(c.topic || '')}')">
        <div class="cluster-topic">${escHtml(c.topic || 'Related Stories')}</div>
        <div class="cluster-meta">
          <span>📰 ${c.article_count} articles · ${c.source_count} sources</span>
          <span class="sentiment-badge" style="background:${sentimentColor};color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem">${capitalize(c.avg_sentiment)}</span>
          ${c.is_underreported ? '<span class="underreported-badge" style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:0.7rem">🔴 Underreported</span>' : ''}
        </div>
      </div>`;
  }).join('');
}

window.filterByCluster = function(topic) {
  const input = document.getElementById('searchInput');
  if (input) {
    input.value = topic;
    state.searchQuery = topic;
    state.currentPage = 1;
    state.hasMore = true;
    loadArticles();
  }
};

// FIX 3: Load Trending Keywords as Tag Cloud
async function loadTrending() {
  const el = document.getElementById('trendingCloud');
  if (!el) return;
  const data = await fetchAPI('/api/trending', { params: { limit: 20 } });
  if (!data || !data.length) {
    el.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem">No trending data.</span>';
    return;
  }

  // FIX 3: Render as tag cloud with size and color based on count
  const max = data[0].count;
  const min = data[data.length - 1].count;

  el.innerHTML = data.map(t => {
    const ratio = (t.count - min) / (max - min || 1);
    const size = 12 + ratio * 16;  // 12px to 28px
    let color;
    if (ratio > 0.75) color = '#dc2626';      // Very high = red
    else if (ratio > 0.5) color = '#ea580c';  // High = orange
    else if (ratio > 0.25) color = '#2563eb'; // Medium = blue
    else color = '#6b7280';                   // Low = gray

    return `<span class="keyword-tag" style="font-size:${size}px;color:${color};cursor:pointer;margin:4px 8px;display:inline-block;font-weight:600"
                  onclick="searchFor('${escHtml(t.keyword || t.word)}')">${escHtml(t.keyword || t.word)} <small style="opacity:0.7">(${t.count})</small></span>`;
  }).join('');
}

window.searchFor = function(word) {
  const input = document.getElementById('searchInput');
  if (input) {
    input.value = word;
    state.searchQuery = word;
    state.currentPage = 1;
    state.hasMore = true;
    loadArticles();
  }
};

function initFilters() {
  document.querySelectorAll('#filterRail .filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#filterRail .filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentCategory = btn.dataset.category;
      state.currentPage = 1;
      state.hasMore = true;
      loadArticles();
    });
  });
}

function initSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;
  input.addEventListener('input', debounce(() => {
    state.searchQuery = input.value.trim();
    state.currentPage = 1;
    state.hasMore = true;
    loadArticles();
  }, 400));
}

function initRefresh() {
  const btn = document.getElementById('refreshBtn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    btn.disabled = true; btn.textContent = '↻ Fetching...';
    await fetchAPI('/api/pipeline/run', { method: 'POST' });
    btn.disabled = false; btn.textContent = '↻ Refresh';
    state.currentPage = 1;
    state.hasMore = true;
    loadStats(); loadArticles(); loadClusters(); loadTrending();
  });
}

function initChat() {
  const fab = document.getElementById('chatFab');
  const panel = document.getElementById('chatPanel');
  const close = document.getElementById('chatClose');
  const input = document.getElementById('chatInput');
  const send = document.getElementById('chatSend');
  if (!fab || !panel) return;

  fab.addEventListener('click', () => panel.classList.toggle('open'));
  close?.addEventListener('click', () => panel.classList.remove('open'));

  const sendMessage = async () => {
    const q = input.value.trim();
    if (!q) return;
    const msgs = document.getElementById('chatMessages');
    msgs.innerHTML += `<div class="chat-msg user">${escHtml(q)}</div>`;
    input.value = '';
    msgs.innerHTML += `<div class="chat-msg ai" id="chatLoading">Thinking...</div>`;
    msgs.scrollTop = msgs.scrollHeight;

    const data = await fetchAPI('/api/chat', { method: 'POST', body: { question: q } });
    const loading = document.getElementById('chatLoading');
    if (loading) loading.remove();
    msgs.innerHTML += `<div class="chat-msg ai">${escHtml(data?.answer || 'Sorry, I couldn\'t process that.')}</div>`;
    msgs.scrollTop = msgs.scrollHeight;
  };
  send?.addEventListener('click', sendMessage);
  input?.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
}

function toggleBookmark(id, btn) {
  const idx = state.bookmarks.indexOf(id);
  if (idx >= 0) { state.bookmarks.splice(idx, 1); btn.textContent = '☆'; btn.classList.remove('bookmarked'); }
  else { state.bookmarks.push(id); btn.textContent = '★'; btn.classList.add('bookmarked'); }
  localStorage.setItem('bookmarks', JSON.stringify(state.bookmarks));
}

// ═══════════════════════════════════════════
// PAGE 2: Market Intelligence (FIX 6)
// ═══════════════════════════════════════════
async function initMarketPage() {
  // Market page has its own inline initialization in market.html
  // Only load sentiment chart here
  loadMarketSentimentChart();
}

async function loadMarketSentimentChart() {
  const ctx = document.getElementById('marketSentimentChart');
  if (!ctx) return;

  const data = await fetchAPI('/api/markets/mood');
  if (!data) return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Negative', 'Neutral'],
      datasets: [{
        data: [data.positive_pct, data.negative_pct, data.neutral_pct],
        backgroundColor: ['#16a34a', '#dc2626', '#6b7280'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

async function loadSectorChart() {
  const ctx = document.getElementById('sectorChart');
  if (!ctx) return;
  const data = await fetchAPI('/api/sector-heatmap');
  if (!data) return;

  const sectors = Object.keys(data);
  const values = Object.values(data);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sectors,
      datasets: [{
        label: 'Sentiment Score',
        data: values,
        backgroundColor: values.map(v => v > 0 ? '#16a34a' : v < 0 ? '#dc2626' : '#6b7280'),
        borderRadius: 6,
      }]
    },
    options: chartOptions('Sentiment Score')
  });
}

// ═══════════════════════════════════════════
// PAGE 3: Prediction Markets (FIX 7)
// ═══════════════════════════════════════════
let allMarkets = [];

async function initPredictionsPage() {
  const data = await fetchAPI('/api/predictions/markets', { params: { limit: 30 } });
  allMarkets = data || [];
  renderMarkets(allMarkets);
  initMarketFilters();
}

function renderMarkets(markets) {
  const el = document.getElementById('marketsList');
  if (!el) return;
  if (!markets.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎯</div><div class="empty-state-text">No prediction markets available.</div></div>';
    return;
  }

  el.innerHTML = markets.map(m => {
    const yes = m.outcomes?.find(o => o.name === 'Yes') || m.outcomes?.[0] || { percent: 50 };
    const no = m.outcomes?.find(o => o.name === 'No') || m.outcomes?.[1] || { percent: 50 };

    const sentimentColor = m.news_sentiment === 'positive' ? '#16a34a' : m.news_sentiment === 'negative' ? '#dc2626' : '#6b7280';

    return `
      <div class="market-card" id="market-${m.id}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span class="market-category-badge">${escHtml(m.category || 'Other')}</span>
          <span class="sentiment-badge" style="background:${sentimentColor};color:white;padding:3px 8px;border-radius:4px;font-size:0.7rem">
            News: ${capitalize(m.news_sentiment)}
          </span>
        </div>
        <h3 class="market-question">${escHtml(m.question)}</h3>
        ${m.description ? `<p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:12px">${escHtml(m.description).slice(0, 200)}</p>` : ''}
        <div class="odds-bar" style="display:flex;border-radius:8px;overflow:hidden;height:40px;margin-bottom:12px">
          <div class="odds-yes" style="background:#16a34a;color:white;display:flex;align-items:center;justify-content:center;width:${Math.max(yes.percent, 5)}%;font-weight:600">Yes ${yes.percent?.toFixed(1)}%</div>
          <div class="odds-no" style="background:#dc2626;color:white;display:flex;align-items:center;justify-content:center;width:${Math.max(no.percent, 5)}%;font-weight:600">No ${no.percent?.toFixed(1)}%</div>
        </div>
        <div class="market-meta" style="display:flex;gap:12px;font-size:0.75rem;color:var(--text-muted);margin-bottom:12px">
          <span>💰 Vol: $${formatNumber(m.volume || 0)}</span>
          <span>💧 Liq: $${formatNumber(m.liquidity || 0)}</span>
          ${m.end_date ? `<span>📅 ${formatDate(m.end_date)}</span>` : ''}
        </div>
        <button class="analyze-btn" onclick="analyzeMarket('${m.id}', '${escHtml(m.question.replace(/'/g, "\\'"))}', ${yes.percent / 100})" style="width:100%;padding:10px;background:#2563eb;color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer">
          🤖 Analyze with AI
        </button>
        <div id="analysis-${m.id}" class="analysis-result" style="display:none;margin-top:12px"></div>
      </div>`;
  }).join('');
}

window.analyzeMarket = async function(marketId, question, yesProbability) {
  const resultDiv = document.getElementById(`analysis-${marketId}`);
  if (!resultDiv) return;

  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">🤖 Analyzing market...</div>';

  const analysis = await fetchAPI('/api/predictions/analyze', {
    method: 'POST',
    body: {
      market_id: marketId,
      question: question,
      yes_probability: yesProbability,
      related_article_ids: []
    }
  });

  if (!analysis) {
    resultDiv.innerHTML = '<div style="color:#dc2626;padding:12px">Analysis failed. Please try again.</div>';
    return;
  }

  const actionColor = analysis.action === 'buy_yes' ? '#16a34a' : analysis.action === 'buy_no' ? '#dc2626' : '#6b7280';
  const riskColor = analysis.risk_level === 'low' ? '#16a34a' : analysis.risk_level === 'high' ? '#dc2626' : '#f59e0b';

  resultDiv.innerHTML = `
    <div style="background:var(--card-bg);border-radius:8px;padding:16px;border-left:4px solid ${actionColor}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <span style="background:${actionColor};color:white;padding:8px 16px;border-radius:6px;font-weight:700;font-size:1rem">${analysis.action.replace('_', ' ').toUpperCase()}</span>
        <span style="background:${riskColor};color:white;padding:6px 12px;border-radius:6px;font-size:0.85rem;font-weight:600">${analysis.risk_level.toUpperCase()} RISK</span>
      </div>
      <div style="margin-bottom:12px">
        <div style="background:var(--bg);border-radius:6px;overflow:hidden;height:8px;margin-bottom:4px">
          <div style="background:${actionColor};height:100%;width:${analysis.confidence * 100}%"></div>
        </div>
        <div style="font-size:0.75rem;color:var(--text-muted)">Confidence: ${Math.round(analysis.confidence * 100)}%</div>
      </div>
      <div style="margin-bottom:12px;color:var(--text-primary)">${escHtml(analysis.reasoning)}</div>
      <div style="margin-bottom:12px">
        <div style="font-weight:600;font-size:0.85rem;margin-bottom:6px;color:var(--text-primary)">Key Factors:</div>
        <ul style="margin:0;padding-left:20px;font-size:0.85rem;color:var(--text-secondary)">
          ${(analysis.key_factors || []).map(f => `<li>${escHtml(f)}</li>`).join('')}
        </ul>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:var(--text-muted)">
        <span>Target: ${escHtml(analysis.price_target || 'N/A')}</span>
        <a href="${escHtml(analysis.polymarket_url || '#')}" target="_blank" style="color:#2563eb;text-decoration:none;font-weight:600">→ Open on Polymarket</a>
      </div>
    </div>`;
};

function initMarketFilters() {
  document.querySelectorAll('#marketFilterRail .filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#marketFilterRail .filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.category;
      renderMarkets(cat === 'all' ? allMarkets : allMarkets.filter(m => m.category === cat));
    });
  });
}

// ═══════════════════════════════════════════
// Chart Helpers
// ═══════════════════════════════════════════
function chartOptions(yLabel) {
  return {
    responsive: true,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: getCSSVar('--text-muted'), font: { family: 'Inter' } } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: getCSSVar('--text-muted'), font: { family: 'Inter' } }, title: { display: !!yLabel, text: yLabel, color: getCSSVar('--text-muted') } },
    }
  };
}

function getCSSVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#94a3b8';
}

// ═══════════════════════════════════════════
// Authentication
// ═══════════════════════════════════════════
const authState = {
  user: JSON.parse(localStorage.getItem('user') || 'null'),
};

function initAuth() {
  const authBtn = document.getElementById('authBtn');
  const authModal = document.getElementById('authModal');
  const authClose = document.getElementById('authClose');
  const tabLogin = document.getElementById('tabLogin');
  const tabRegister = document.getElementById('tabRegister');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');

  if (!authBtn || !authModal) return;

  // Update auth button based on login state
  updateAuthButton();

  // Open modal
  authBtn.addEventListener('click', () => {
    if (authState.user) {
      // User is logged in - show options or logout
      if (confirm(`Logged in as ${authState.user.username}. Logout?`)) {
        logout();
      }
    } else {
      authModal.classList.add('active');
    }
  });

  // Close modal
  authClose?.addEventListener('click', () => {
    authModal.classList.remove('active');
  });

  // Close on outside click
  authModal.addEventListener('click', (e) => {
    if (e.target === authModal) {
      authModal.classList.remove('active');
    }
  });

  // Tab switching
  tabLogin?.addEventListener('click', () => {
    tabLogin.classList.add('active');
    tabRegister?.classList.remove('active');
    loginForm?.classList.add('active');
    registerForm?.classList.remove('active');
  });

  tabRegister?.addEventListener('click', () => {
    tabRegister.classList.add('active');
    tabLogin?.classList.remove('active');
    registerForm?.classList.add('active');
    loginForm?.classList.remove('active');
  });

  // Login form submission
  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername')?.value;
    const password = document.getElementById('loginPassword')?.value;
    const errorDiv = document.getElementById('loginError');

    if (!username || !password) {
      if (errorDiv) errorDiv.textContent = 'Please enter username and password';
      return;
    }

    try {
      const response = await fetchAPI('/api/auth/login', {
        method: 'POST',
        body: { username, password }
      });

      if (response && response.id) {
        // Login successful
        authState.user = response;
        localStorage.setItem('user', JSON.stringify(response));
        authModal.classList.remove('active');
        updateAuthButton();
        showSuccess(`Welcome back, ${response.username}!`);

        // Reload articles with personalized feed
        state.currentPage = 1;
        loadArticles();
      } else {
        if (errorDiv) errorDiv.textContent = 'Login failed. Please try again.';
      }
    } catch (error) {
      if (errorDiv) errorDiv.textContent = 'Invalid username or password';
    }
  });

  // Register form submission
  registerForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername')?.value;
    const password = document.getElementById('regPassword')?.value;
    const region = document.getElementById('regRegion')?.value;
    const interests = Array.from(document.querySelectorAll('.interest-cb:checked')).map(cb => cb.value);
    const errorDiv = document.getElementById('regError');

    if (!username || !password) {
      if (errorDiv) errorDiv.textContent = 'Please enter username and password';
      return;
    }

    try {
      const response = await fetchAPI('/api/auth/register', {
        method: 'POST',
        body: { username, password, region, interests }
      });

      if (response && response.id) {
        // Registration successful
        authState.user = response;
        localStorage.setItem('user', JSON.stringify(response));
        authModal.classList.remove('active');
        updateAuthButton();
        showSuccess(`Account created! Welcome, ${response.username}!`);

        // Reload articles with personalized feed
        state.currentPage = 1;
        loadArticles();
      } else {
        if (errorDiv) errorDiv.textContent = 'Registration failed. Username may already exist.';
      }
    } catch (error) {
      if (errorDiv) errorDiv.textContent = 'Registration failed. Please try again.';
    }
  });
}

function updateAuthButton() {
  const authBtn = document.getElementById('authBtn');
  if (!authBtn) return;

  if (authState.user) {
    authBtn.textContent = `👤 ${authState.user.username}`;
    authBtn.classList.add('logged-in');
  } else {
    authBtn.textContent = 'Login';
    authBtn.classList.remove('logged-in');
  }
}

function logout() {
  authState.user = null;
  localStorage.removeItem('user');
  updateAuthButton();
  showSuccess('Logged out successfully');

  // Reload articles without personalization
  state.currentPage = 1;
  loadArticles();
}

function showSuccess(message) {
  const toast = document.createElement('div');
  toast.className = 'success-toast';
  toast.textContent = message;
  toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#16a34a;color:white;padding:12px 20px;border-radius:8px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.3)';
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ═══════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function escHtml(str) { if (!str) return ''; const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
