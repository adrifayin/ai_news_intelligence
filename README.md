# ⚡ DataStraw - AI-Powered News Intelligence Platform

Real-time news aggregation with AI analysis, sentiment tracking, and market intelligence.

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/adrifayin/ai_news_intelligence.git
cd ai_news_intelligence

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run application
cd backend
python main.py
```

Visit: http://localhost:8000

---

## 🌐 Deploy on Railway (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

**One-click deployment:**

1. Click "Deploy on Railway" button
2. Connect your GitHub account
3. Add environment variables:
   - `GROQ_API_KEY` - Get from https://console.groq.com
   - `NEWSDATA_API_KEY` - Get from https://newsdata.io
   - `OPENWEATHER_API_KEY` - Get from https://openweathermap.org
4. Deploy! 🚀

Your app will be live in ~2 minutes.

**See [RAILWAY_DEPLOYMENT_FIXED.md](RAILWAY_DEPLOYMENT_FIXED.md) for detailed guide.**

---

## 🔑 API Keys (Free Tier)

1. **Groq AI** - https://console.groq.com
   - Free: 30 requests/minute
   - Powers AI summaries & chat

2. **NewsData.io** - https://newsdata.io
   - Free: 200 requests/day
   - Real-time news aggregation

3. **OpenWeather** - https://openweathermap.org/api (optional)
   - Free: 1000 requests/day
   - Weather context data

---

## ✨ Features

### 📰 News Dashboard
- **Real-time Aggregation** - Multi-source news fetching
- **AI Summaries** - Click-to-process with Llama 3.1
- **Sentiment Analysis** - Automatic classification
- **Story Clusters** - Related article grouping
- **Trending Keywords** - Tag cloud visualization
- **Infinite Scroll** - Smooth browsing

### 📈 Market Intelligence
- **Ticker Sentiment** - AI analysis of stock mentions
- **Buy/Sell Signals** - Automated recommendations
- **Sector Heatmap** - Industry sentiment breakdown
- **Market Mood** - Overall sentiment score (0-100)
- **Smart Filtering** - Sort by signals, sentiment, mentions

### 🤖 AI Chat
- **Natural Language Queries** - Ask questions about news
- **Context-Aware** - Answers from actual articles
- **Powered by Groq** - Fast Llama 3.1 inference

---

## 📦 Tech Stack

**Backend:** FastAPI, SQLAlchemy, SQLite  
**Frontend:** Vanilla JavaScript, Chart.js  
**AI:** Groq (Llama 3.1 8B), TextBlob  
**APIs:** NewsData.io, OpenWeather  
**Deployment:** Railway, Render, or any Python platform

---

## 📁 Project Structure

```
ai_news_intelligence/
├── backend/              # Python FastAPI backend
│   ├── main.py           # Application entry point
│   ├── database.py       # Models & database
│   ├── ai_processor.py   # AI summarization
│   ├── pipeline.py       # News fetching
│   ├── market.py         # Market analysis
│   └── ...
├── frontend/             # Static frontend
│   ├── index.html        # News dashboard
│   ├── market.html       # Market intelligence
│   ├── predictions.html  # Predictions
│   ├── app.js            # JavaScript
│   └── style.css         # Styling
├── screenshots/          # Project images
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── runtime.txt           # Python version (3.11)
├── Procfile              # Process configuration
└── README.md             # This file
```

---

## 🎯 API Endpoints

```
GET  /                       # Homepage
GET  /market                 # Market intelligence
GET  /predictions            # Predictions page
GET  /docs                   # API documentation (Swagger)

GET  /api/articles           # List articles with filters
GET  /api/articles/{id}      # Get single article
GET  /api/stats              # Dashboard statistics
GET  /api/markets/mood       # Market sentiment
GET  /api/markets/tickers    # Ticker analysis
POST /api/pipeline/run       # Fetch new articles
POST /api/chat               # Chat with AI
```

---

## 🔧 Environment Variables

Required variables in `.env`:

```env
# AI Processing
GROQ_API_KEY=your_groq_api_key

# News Data
NEWSDATA_API_KEY=your_newsdata_api_key

# Weather (optional)
OPENWEATHER_API_KEY=your_openweather_api_key

# Database
DATABASE_URL=sqlite:///./news_intelligence.db

# Security
JWT_SECRET_KEY=your-random-secret-key

# Environment
ENVIRONMENT=production
```

---

## 🐛 Troubleshooting

### Server Issues
```bash
# Check if running in backend directory
cd backend
python main.py
```

### No Articles Showing
```bash
# Manually trigger news fetch
curl -X POST http://localhost:8000/api/pipeline/run
# Or click "Refresh" button in UI
```

### Module Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### API Key Errors
```bash
# Verify .env file
cat .env | grep API_KEY
```

---

## 🚢 Other Deployment Options

### Render
```yaml
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Heroku
```bash
heroku create datastraw-ai
git push heroku main
heroku config:set GROQ_API_KEY=xxx
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 📧 Contact

- **GitHub:** [@adrifayin](https://github.com/adrifayin)
- **Repository:** https://github.com/adrifayin/ai_news_intelligence
- **Issues:** [Report bugs](https://github.com/adrifayin/ai_news_intelligence/issues)

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Groq](https://groq.com/) - Fast AI inference
- [NewsData.io](https://newsdata.io/) - News API
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [Railway](https://railway.app/) - Deployment platform

---

**Built with ⚡ by DataStraw Team**

*Star this repo if you find it useful!* ⭐
