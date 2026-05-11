# ⚡ DataStraw - AI-Powered News Intelligence Platform

Real-time news aggregation with AI analysis, sentiment tracking, and market intelligence.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Deployed](https://img.shields.io/badge/Deploy-PythonAnywhere-success.svg)

**🌐 Live Demo:** Deploy your own in 10 minutes (100% FREE)

---

## 🚀 Quick Start (Under 5 Minutes)

### Local Development

```bash
# 1. Clone & Install
git clone https://github.com/adrifayin/ai_news_intelligence.git
cd ai_news_intelligence
pip install -r requirements.txt

# 2. Configure API Keys
cp .env.example .env
# Edit .env and add your API keys

# 3. Run
cd backend
python main.py

# 4. Open Browser
# Visit: http://localhost:8000
```

**Done!** 🎉 You should see the news dashboard.

---

## 🌍 Deploy to Production (FREE)

### Recommended: PythonAnywhere (100% FREE Forever)

Deploy in 10 minutes with our detailed guides:

📖 **[Quick Start Guide](QUICK_START_PYTHONANYWHERE.md)** - 10 minutes  
📖 **[Complete Deployment Guide](PYTHONANYWHERE_DEPLOY.md)** - Detailed walkthrough  
✅ **[Deployment Checklist](DEPLOYMENT_CHECKLIST_PA.md)** - Interactive checklist

**Why PythonAnywhere?**
- ✅ 100% FREE forever (no credit card)
- ✅ Never sleeps (always online)
- ✅ HTTPS included
- ✅ 512MB storage
- ✅ 100,000 API calls/day
- ✅ Perfect for portfolios

**Other Options:** See [docs/](docs/) folder for Vercel, Render, and other platforms.

---

## 🔑 Get Free API Keys (2 minutes)

1. **Groq (AI)** - https://console.groq.com
   - Sign up → Create API key → Copy to `.env`
   - Free tier: 30 requests/minute

2. **NewsData.io (News)** - https://newsdata.io
   - Sign up → Copy API key from dashboard
   - Free tier: 200 requests/day

3. **OpenWeather (Weather)** - https://openweathermap.org/api
   - Sign up → API Keys tab → Copy key
   - Free tier: 1000 requests/day

---

## ✨ Features

### 📰 News Dashboard
- **Real-time Aggregation** - Fetches from multiple news APIs
- **AI Summaries** - Click-to-process (saves 85% API calls)
- **Sentiment Analysis** - Automatic positive/negative/neutral classification
- **Story Clusters** - Groups related articles
- **Trending Keywords** - Tag cloud visualization
- **Infinite Scroll** - Smooth browsing experience

### 📈 Market Intelligence
- **Ticker Sentiment** - AI analysis of stock mentions
- **Buy/Sell Signals** - Automated recommendations with confidence
- **Sector Heatmap** - Industry sentiment breakdown
- **Market Mood** - Overall sentiment score (0-100)
- **Smart Filtering** - Sort by signals, sentiment, mentions

### 🤖 AI Chat
- **Ask Questions** - Query your news database naturally
- **Context-Aware** - Answers from actual articles
- **Powered by Llama 3.1** - Via Groq API

### 🔐 User System
- **Authentication** - Login/register with JWT
- **Personalization** - Region & interest preferences

---

## 📦 Tech Stack

**Backend:** FastAPI, SQLAlchemy, SQLite  
**Frontend:** Vanilla JS, Chart.js  
**AI:** Groq (Llama 3.1 8B), TextBlob  
**APIs:** NewsData.io, OpenWeather

---

## 📁 Project Structure

```
datastraw/
├── backend/              # Python backend (20+ files)
│   ├── main.py           # FastAPI app entry point
│   ├── database.py       # Models & queries
│   ├── ai_processor.py   # AI summarization
│   ├── pipeline.py       # News fetching
│   ├── market.py         # Market analysis
│   └── ...
├── frontend/             # Frontend assets
│   ├── index.html        # News dashboard
│   ├── market.html       # Market page
│   ├── predictions.html  # Predictions page
│   ├── app.js            # Main JavaScript
│   └── style.css         # Styles
├── docs/                 # Additional documentation
├── .env.example          # Config template
├── requirements.txt      # Dependencies
├── wsgi_pythonanywhere.py # PythonAnywhere WSGI config
└── README.md             # This file
```

---

## 🎯 Usage

### Fetch News
```bash
curl -X POST http://localhost:8000/api/pipeline/run
```
Or click **"↻ Refresh"** in the UI

### Process Articles with AI
1. Articles load with sentiment automatically
2. Click **"🤖 Get AI Summary & Insights"** on any card
3. Wait 2-5 seconds for AI processing
4. Summary appears (cached for future views)

### View Market Intelligence
Visit `http://localhost:8000/market` for:
- 20 ticker cards with AI recommendations
- Sector sentiment bar chart
- Market mood score
- Top mentioned stocks

---

## 📊 API Endpoints

```
GET  /                       # Frontend homepage
GET  /market                 # Market intelligence page
GET  /predictions            # Predictions page
GET  /docs                   # API documentation (Swagger UI)

GET  /api/articles           # List articles with filters
GET  /api/articles/{id}      # Get article (?process=true for AI)
GET  /api/stats              # Dashboard statistics
GET  /api/markets/mood       # Market sentiment score
GET  /api/markets/tickers    # Ticker analysis
POST /api/pipeline/run       # Fetch new articles
POST /api/chat               # Ask questions
```

---

## 🔧 Configuration

### Environment Variables
See `.env.example` for all options. Minimum required:
- `GROQ_API_KEY` - AI processing
- `NEWSDATA_API_KEY` - News fetching
- `OPENWEATHER_API_KEY` - Weather data (optional)

### Performance Tuning
Edit `backend/config.py`:
- `MAX_ARTICLES_PER_REQUEST` - Articles per page (default: 20)
- `GROQ_MODEL` - AI model (default: llama-3.1-8b-instant)

---

## 🐛 Troubleshooting

**Server won't start?**
```bash
cd backend
python main.py
# Make sure you're in the backend/ directory
```

**No articles showing?**
```bash
curl -X POST http://localhost:8000/api/pipeline/run
# Or click Refresh button in UI
```

**API key errors?**
```bash
# Check .env file has valid keys
cat .env | grep API_KEY
```

**Module not found errors?**
```bash
pip install -r requirements.txt
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

MIT License - See [LICENSE](LICENSE) file for details

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
- [Chart.js](https://www.chartjs.org/) - Beautiful charts
- [PythonAnywhere](https://www.pythonanywhere.com/) - FREE hosting platform

---

## 📚 Documentation

- **[Deployment Guide](PYTHONANYWHERE_DEPLOY.md)** - Complete PythonAnywhere deployment
- **[Quick Start](QUICK_START_PYTHONANYWHERE.md)** - 10-minute deployment
- **[Checklist](DEPLOYMENT_CHECKLIST_PA.md)** - Step-by-step checklist
- **[Additional Docs](docs/)** - Other platform guides

---

**Built with ⚡ by DataStraw Team**

*Star this repo if you find it useful!* ⭐
