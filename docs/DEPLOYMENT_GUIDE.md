# 🚀 Complete Deployment Guide - DataStraw

Deploy DataStraw with **Render (Backend)** + **Vercel (Frontend)** for FREE!

---

## 📋 Deployment Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Vercel         │ ──API──>│  Render         │
│  (Frontend)     │         │  (Backend API)  │
│  Static HTML    │         │  FastAPI + DB   │
└─────────────────┘         └─────────────────┘
```

**Why this stack?**
- ✅ Completely FREE for this project size
- ✅ Auto-deploy from GitHub
- ✅ Global CDN for fast loading
- ✅ Automatic HTTPS/SSL
- ✅ Zero maintenance

---

## 🎯 Prerequisites

Before starting:
- ✅ GitHub repository: https://github.com/adrifayin/ai_news_intelligence
- ✅ API keys ready:
  - Groq API: https://console.groq.com
  - NewsData.io API: https://newsdata.io/api-keys
  - OpenWeather API (optional): https://openweathermap.org/api
- ✅ Render account: https://render.com
- ✅ Vercel account: https://vercel.com

---

## 🔧 Part 1: Deploy Backend on Render

### Step 1: Deploy Using Blueprint (Easiest)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/blueprints

2. **Create New Blueprint**
   - Click **"New Blueprint Instance"**
   - Connect your GitHub account if not already connected
   - Select repository: `adrifayin/ai_news_intelligence`
   - Branch: `main`
   - Render will automatically detect `render.yaml`
   - Click **"Apply"**

3. **Configure Environment Variables**

   Render will prompt for these variables:

   ```
   GROQ_API_KEY=gsk_your_groq_key_here
   NEWSDATA_API_KEY=pub_your_newsdata_key_here
   OPENWEATHER_API_KEY=your_openweather_key_here (optional)
   DATABASE_URL=sqlite:///./news_intelligence.db
   ```

4. **Deploy**
   - Click **"Create New Resources"**
   - Wait 3-5 minutes for deployment
   - Your backend will be live at: `https://your-app-name.onrender.com`

### Step 2: Test Backend

Visit these endpoints to verify:
- Health check: `https://your-app-name.onrender.com/`
- API docs: `https://your-app-name.onrender.com/docs`
- Test endpoint: `https://your-app-name.onrender.com/api/articles`

### Step 3: Note Your Backend URL

**IMPORTANT:** Copy your Render URL - you'll need it for Vercel!

Example: `https://datastraw-backend.onrender.com`

---

## 🌐 Part 2: Deploy Frontend on Vercel

### Step 1: Import Project

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard

2. **Add New Project**
   - Click **"Add New..."** → **"Project"**
   - Import from GitHub: `adrifayin/ai_news_intelligence`
   - Click **"Import"**

### Step 2: Configure Build Settings

```
Framework Preset: Other
Root Directory: ./
Build Command: (leave empty)
Output Directory: frontend
Install Command: (leave empty)
```

### Step 3: Update vercel.json with Render URL

Before deploying, update the `vercel.json` file with your Render backend URL:

```json
{
  "version": 2,
  "buildCommand": "echo 'Static frontend - no build needed'",
  "outputDirectory": "frontend",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-RENDER-APP.onrender.com/api/:path*"
    }
  ]
}
```

Replace `YOUR-RENDER-APP` with your actual Render service name.

**Commit and push this change to GitHub** before deploying on Vercel.

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes
3. Frontend will be live at: `https://your-project.vercel.app`

---

## 🔗 Part 3: Connect Backend and Frontend

### Update Backend CORS

To allow your Vercel frontend to call the Render backend:

1. Update `backend/main.py` CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-project.vercel.app",  # Add your Vercel URL
        "*"  # Or use wildcard for public API
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Commit and push changes
3. Render will auto-redeploy (takes 2-3 minutes)

### Verify Connection

1. Visit your Vercel URL: `https://your-project.vercel.app`
2. Open browser console (F12)
3. Check for API calls - should see requests to Render backend
4. Verify no CORS errors

---

## ✅ Part 4: Verify Full Deployment

Test all features:

### Frontend (Vercel)
- [ ] Homepage loads with news articles
- [ ] Market page shows data and charts
- [ ] Predictions page displays forecasts
- [ ] Chat feature works
- [ ] Search functionality works
- [ ] Theme toggle works

### Backend (Render)
- [ ] API endpoints respond
- [ ] Articles are fetched from NewsData.io
- [ ] Sentiment analysis works
- [ ] Database stores data
- [ ] AI chat responses work

### Integration
- [ ] Frontend successfully calls backend API
- [ ] No CORS errors in console
- [ ] Data loads on all pages
- [ ] Real-time updates work

---

## 🔄 Auto-Deployment

Both platforms auto-deploy when you push to GitHub:

**Vercel:**
- Push to `main` → Production deployment
- Push to other branches → Preview deployment

**Render:**
- Push to `main` → Automatic backend redeploy
- Takes 2-5 minutes to complete

---

## 📊 Free Tier Limits

### Render Free Tier
- 512 MB RAM
- 0.1 CPU
- 750 hours/month (sleeps after 15 min inactivity)
- Auto-wakes on request (takes 30-60 seconds)
- 100 GB bandwidth/month

### Vercel Free Tier
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic SSL
- Global CDN
- Analytics included

**Perfect for this project!** 🎉

---

## 🐛 Troubleshooting

### Backend Issues

**"Application failed to respond" on Render**
- Check logs: Dashboard → Your Service → Logs
- Verify environment variables are set
- Ensure `requirements.txt` has all dependencies
- Check Python version in `runtime.txt`

**Database not persisting data**
- Render free tier resets filesystem on redeploy
- Consider upgrading to paid tier for persistent storage
- Or use external database (PostgreSQL on Render)

**API endpoints return 404**
- Verify routes in `backend/main.py`
- Check API docs at `/docs`
- Ensure imports are correct (no `backend.` prefix)

### Frontend Issues

**API calls fail with CORS errors**
- Update backend CORS to allow Vercel domain
- Redeploy backend after CORS changes
- Check `vercel.json` has correct Render URL

**Frontend shows but no data loads**
- Verify `vercel.json` rewrites point to correct Render URL
- Check browser console for errors
- Test backend API directly in browser

**404 on page refresh**
- Vercel should handle this with rewrites
- Check `vercel.json` configuration

### Deployment Issues

**Render build fails**
- Check logs for specific error
- Verify `requirements.txt` is complete
- Ensure Python version matches `runtime.txt`

**Vercel deployment fails**
- Ensure `frontend/` directory exists
- Check no build command is causing issues
- Verify file paths are correct

---

## 🎯 Custom Domains (Optional)

### Render
1. Go to Service Settings → Custom Domain
2. Add your domain
3. Update DNS records as shown
4. SSL is automatic

### Vercel
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records
4. SSL is automatic

---

## 📈 Monitoring & Logs

### Render Logs
- Dashboard → Your Service → Logs
- Shows real-time backend logs
- Filter by error level

### Vercel Logs
- Dashboard → Your Project → Deployments
- Click deployment → View Function Logs
- Analytics tab for traffic stats

---

## 💡 Optimization Tips

1. **Reduce Backend Sleep Time**
   - Free tier sleeps after 15 minutes
   - Add uptime monitoring (UptimeRobot) to ping every 10 min
   - Or upgrade to paid tier ($7/month)

2. **Cache API Responses**
   - Add caching headers to reduce API calls
   - Use localStorage for frequently accessed data

3. **Optimize Assets**
   - Compress images before uploading
   - Minify CSS/JS (Vercel does this automatically)

4. **Use Environment Variables**
   - Never commit API keys
   - Use platform-specific env vars

---

## 🎉 Success!

Your DataStraw platform is now live!

**URLs:**
- Frontend: `https://your-project.vercel.app`
- Backend API: `https://your-app-name.onrender.com`
- API Docs: `https://your-app-name.onrender.com/docs`

**Share your project:**
- Add to GitHub README
- Share on social media
- Add to portfolio

---

## 📚 Additional Resources

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- GitHub Actions: https://docs.github.com/actions

---

## 🆘 Need Help?

- Check logs on Render/Vercel dashboards
- Review error messages in browser console
- Test backend API endpoints directly
- Verify all environment variables are set
- Ensure CORS is properly configured

---

**Good luck with your deployment!** 🚀

If everything is configured correctly, your platform should be live and fully functional within 10-15 minutes!
