# 🚀 Render Manual Deployment (Without Blueprint)

Since your git repository structure has the project in a subdirectory, Blueprint deployment is causing issues. Here's how to deploy manually:

---

## 📋 Manual Deployment Steps

### 1. Go to Render Dashboard

Visit: https://dashboard.render.com

### 2. Create New Web Service (NOT Blueprint)

1. Click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"** or **"Configure account"**
3. Select your GitHub account
4. Choose repository: **`ai_news_intelligence`**
5. Click **"Connect"**

### 3. Configure Service Settings

Fill in these exact settings:

```
Name: datastraw-backend
Region: Oregon (US West)
Branch: main
Root Directory: Desktop/PROJECTS/DATA STRAW AI-Powered News Intelligence Platform
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**IMPORTANT:** Set `Root Directory` to:
```
Desktop/PROJECTS/DATA STRAW AI-Powered News Intelligence Platform
```

### 4. Choose Free Plan

- Instance Type: **Free**
- Click **"Advanced"** to set environment variables

### 5. Add Environment Variables

Click **"Add Environment Variable"** for each:

```
PYTHON_VERSION = 3.11.0
GROQ_API_KEY = your_groq_key_here
NEWSDATA_API_KEY = your_newsdata_key_here
OPENWEATHER_API_KEY = your_openweather_key_here (optional)
DATABASE_URL = sqlite:///./news_intelligence.db
```

### 6. Create Web Service

Click **"Create Web Service"** at the bottom.

Render will:
- Clone your repository
- Navigate to the root directory you specified
- Install dependencies from `requirements.txt`
- Start your FastAPI backend

---

## ✅ After Deployment

### Get Your Backend URL

Once deployed, you'll get a URL like:
```
https://datastraw-backend.onrender.com
```

### Test Backend

Visit these endpoints:
- `https://your-app.onrender.com/`
- `https://your-app.onrender.com/docs`
- `https://your-app.onrender.com/api/articles`

### Update Vercel

Update `vercel.json` with your actual Render URL:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://datastraw-backend.onrender.com/api/$1"
    }
  ]
}
```

Then push to GitHub:
```bash
git add vercel.json
git commit -m "config: Update Render backend URL"
git push origin main
```

---

## 🎯 Why Manual Deploy Works

**Blueprint Issue:**
- Reads `render.yaml` from git root
- Git root is at `C:\Users\ADHIL` (your home directory)
- Can't properly handle the nested path with spaces

**Manual Deploy:**
- You directly specify the `Root Directory` in the UI
- Render navigates to that directory before building
- Works correctly with nested paths

---

## 🔄 Auto-Deploy Setup

After first deployment:
1. Go to your service settings
2. Auto-deploy is enabled by default
3. Every push to `main` branch will trigger redeploy

---

## 📊 Monitor Deployment

Watch the logs during deployment:
1. Dashboard → Your Service
2. Click **"Logs"** tab
3. Watch for:
   - ✅ Cloning repository
   - ✅ Checking out to root directory
   - ✅ Installing requirements
   - ✅ Starting server

---

## 🐛 Troubleshooting

**Still can't find requirements.txt?**

Try these root directory formats:
```
Desktop/PROJECTS/DATA STRAW AI-Powered News Intelligence Platform
./Desktop/PROJECTS/DATA STRAW AI-Powered News Intelligence Platform
"Desktop/PROJECTS/DATA STRAW AI-Powered News Intelligence Platform"
```

**Python version wrong?**

Add this to environment variables:
```
PYTHON_VERSION = 3.11.0
```

**Build succeeds but app won't start?**

Check the start command:
```
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

---

## 💡 Better Long-Term Solution

**Reorganize Git Repository** (Recommended)

Your git repo should be at the project root, not your home directory:

```bash
# This is the PROPER way:
cd "C:\Users\ADHIL\Desktop\PROJECTS\DATA STRAW AI-Powered News Intelligence Platform"
git init
git remote add origin https://github.com/adrifayin/ai_news_intelligence.git

# Then you can use Blueprint without issues
```

But for now, manual deploy will work! 🚀

---

## ✅ Success Checklist

- [ ] Created Web Service on Render (not Blueprint)
- [ ] Set Root Directory to project path
- [ ] Added all environment variables
- [ ] Build succeeded
- [ ] Backend is live
- [ ] Tested `/docs` endpoint
- [ ] Updated vercel.json with backend URL
- [ ] Pushed vercel.json to GitHub

---

**Total Time:** ~10 minutes

Once deployed, you'll have a working backend API! 🎉
