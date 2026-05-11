# ✅ Deployment Checklist

Quick checklist to deploy DataStraw in 15 minutes.

---

## 🎯 Before You Start

Gather these:
- [ ] GitHub repo URL: https://github.com/adrifayin/ai_news_intelligence
- [ ] Groq API key from https://console.groq.com
- [ ] NewsData.io API key from https://newsdata.io
- [ ] Render account (free signup)
- [ ] Vercel account (free signup)

---

## 🔧 Part 1: Deploy Backend (5 mins)

- [ ] Go to https://dashboard.render.com/blueprints
- [ ] Click "New Blueprint Instance"
- [ ] Connect GitHub and select your repo
- [ ] Enter environment variables:
  ```
  GROQ_API_KEY=gsk_xxxxx
  NEWSDATA_API_KEY=pub_xxxxx
  DATABASE_URL=sqlite:///./news_intelligence.db
  ```
- [ ] Click "Apply" and wait for deployment
- [ ] Copy your backend URL: `https://______.onrender.com`
- [ ] Test: Visit `/docs` endpoint

---

## 🌐 Part 2: Update Config (2 mins)

- [ ] Open `vercel.json` in your repo
- [ ] Replace `YOUR-RENDER-APP` with your Render service name
- [ ] Commit and push to GitHub:
  ```bash
  git add vercel.json
  git commit -m "config: Update Render backend URL"
  git push origin main
  ```

---

## 🚀 Part 3: Deploy Frontend (5 mins)

- [ ] Go to https://vercel.com/dashboard
- [ ] Click "Add New..." → "Project"
- [ ] Import your GitHub repo
- [ ] Configure settings:
  - Build Command: (empty)
  - Output Directory: `frontend`
- [ ] Click "Deploy"
- [ ] Wait for deployment
- [ ] Copy your frontend URL: `https://______.vercel.app`

---

## 🔗 Part 4: Connect Services (3 mins)

- [ ] Open `backend/main.py`
- [ ] Update CORS to include your Vercel URL:
  ```python
  allow_origins=[
      "https://your-project.vercel.app",
      "*"
  ]
  ```
- [ ] Commit and push:
  ```bash
  git add backend/main.py
  git commit -m "config: Update CORS for Vercel"
  git push origin main
  ```
- [ ] Wait for Render auto-redeploy (2-3 mins)

---

## ✅ Part 5: Verify (5 mins)

Test your deployed app:

- [ ] Visit your Vercel URL
- [ ] Homepage loads with news articles
- [ ] No CORS errors in console (F12)
- [ ] Market page shows charts
- [ ] Predictions page works
- [ ] Chat feature responds
- [ ] Search works

---

## 🎉 Done!

Your app is now live!

**Frontend:** https://your-project.vercel.app
**Backend:** https://your-app.onrender.com
**API Docs:** https://your-app.onrender.com/docs

---

## ⚠️ Common Issues

**Backend shows "Application failed to respond"**
→ Check Render logs, verify env variables

**Frontend loads but no data**
→ Check vercel.json has correct Render URL
→ Verify CORS in backend

**CORS errors in console**
→ Update backend CORS, redeploy Render

---

## 📱 Next Steps

- [ ] Add custom domain (optional)
- [ ] Set up uptime monitoring (optional)
- [ ] Share your project URL
- [ ] Update README with live demo link

---

**Total time: ~15-20 minutes** ⏱️

Need detailed help? See `DEPLOYMENT_GUIDE.md`
