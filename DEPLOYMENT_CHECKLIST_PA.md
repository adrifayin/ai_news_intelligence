# ✅ PythonAnywhere Deployment Checklist

Use this checklist while deploying to ensure you don't miss any steps.

---

## 📋 Pre-Deployment (5 minutes)

- [ ] **GitHub repo is ready:** https://github.com/adrifayin/ai_news_intelligence
- [ ] **Get API Keys:**
  - [ ] Groq API Key from https://console.groq.com
  - [ ] NewsData.io API Key from https://newsdata.io/api-keys
  - [ ] OpenWeather API Key from https://openweathermap.org/api (optional)
- [ ] **Save your API keys** in a text file temporarily

---

## 🚀 Deployment Steps (10 minutes)

### Step 1: Sign Up
- [ ] Go to https://www.pythonanywhere.com/registration/register/beginner/
- [ ] Choose username: `_________________`
- [ ] Your URL will be: `https://__________.pythonanywhere.com`
- [ ] Verify email
- [ ] Log in to dashboard

### Step 2: Clone Repository
- [ ] Open Bash console (Consoles tab → Bash)
- [ ] Run: `git clone https://github.com/adrifayin/ai_news_intelligence.git`
- [ ] Run: `cd ai_news_intelligence`
- [ ] Verify files: `ls -la` (should see backend/, frontend/, etc.)

### Step 3: Install Dependencies
- [ ] Run: `pip3.10 install --user -r requirements.txt`
- [ ] Wait 2-3 minutes for installation
- [ ] Check for any errors in output

### Step 4: Create .env File
- [ ] Run: `nano .env`
- [ ] Paste your API keys:
```env
GROQ_API_KEY=gsk_your_key_here
NEWSDATA_API_KEY=pub_your_key_here
OPENWEATHER_API_KEY=your_key_here
DATABASE_URL=sqlite:///./news_intelligence.db
JWT_SECRET_KEY=random-secret-string-here
ENVIRONMENT=production
```
- [ ] Save: `Ctrl+X` → `Y` → `Enter`
- [ ] Verify: `cat .env` (check keys are there)

### Step 5: Create Web App
- [ ] Go to "Web" tab
- [ ] Click "Add a new web app"
- [ ] Click "Next" (accept default domain)
- [ ] Choose "Manual configuration"
- [ ] Select "Python 3.10"
- [ ] Click "Next"
- [ ] Note success message

### Step 6: Configure WSGI File
- [ ] On Web tab, find "Code" section
- [ ] Click WSGI configuration file link
- [ ] DELETE all existing content
- [ ] Copy content from `wsgi_pythonanywhere.py` file in your repo
- [ ] **⚠️ IMPORTANT:** Replace `yourusername` with your actual username (line 11)
- [ ] Click "Save" at top

### Step 7: Set Paths
**Source Code:**
- [ ] Web tab → Code section → Source code
- [ ] Set to: `/home/yourusername/ai_news_intelligence`
- [ ] Replace `yourusername` with yours

**Working Directory:**
- [ ] Web tab → Code section → Working directory
- [ ] Set to: `/home/yourusername/ai_news_intelligence/backend`

**Static Files:**
- [ ] Web tab → Static files section
- [ ] Click "Enter URL"
- [ ] URL: `/`
- [ ] Directory: `/home/yourusername/ai_news_intelligence/frontend`
- [ ] Click checkmark to save

### Step 8: Initialize Database
- [ ] Back to Bash console
- [ ] Run: `cd ~/ai_news_intelligence/backend`
- [ ] Run: `python3.10 -c "from database import init_db; init_db()"`
- [ ] Check for success message (no errors)

### Step 9: Reload & Launch
- [ ] Go to Web tab
- [ ] Click big green "Reload" button at top
- [ ] Wait 10-15 seconds

---

## ✅ Verification (5 minutes)

### Test Your Deployment:

- [ ] **Homepage loads:**
  - Visit: `https://yourusername.pythonanywhere.com/`
  - Should see DataStraw dashboard
  
- [ ] **API documentation works:**
  - Visit: `https://yourusername.pythonanywhere.com/docs`
  - Should see Swagger UI
  
- [ ] **Market page loads:**
  - Visit: `https://yourusername.pythonanywhere.com/market`
  - Should see market intelligence page
  
- [ ] **Predictions page loads:**
  - Visit: `https://yourusername.pythonanywhere.com/predictions`
  - Should see predictions interface

### Check for Errors:
- [ ] Web tab → Error log → No recent errors
- [ ] Web tab → Server log → See successful requests
- [ ] Browser console (F12) → No JavaScript errors

---

## 🐛 Troubleshooting

If something doesn't work, check these:

### ❌ 500 Error / "Something went wrong"
- [ ] Check Web tab → Error log
- [ ] Look for Python import errors
- [ ] Verify WSGI file has correct username
- [ ] Check all paths are absolute (start with `/home/`)

### ❌ "No module named 'fastapi'"
- [ ] Reinstall: `pip3.10 install --user -r requirements.txt`
- [ ] Check for errors during installation
- [ ] Reload web app

### ❌ Static files not loading
- [ ] Web tab → Static files section
- [ ] Verify path: `/home/yourusername/ai_news_intelligence/frontend`
- [ ] Check files exist: `ls ~/ai_news_intelligence/frontend/`
- [ ] Reload web app

### ❌ Database errors
- [ ] Recreate database:
```bash
cd ~/ai_news_intelligence/backend
rm -f news_intelligence.db
python3.10 -c "from database import init_db; init_db()"
```
- [ ] Reload web app

### ❌ API keys not working
- [ ] Check .env file: `cat ~/ai_news_intelligence/.env`
- [ ] Or set directly in WSGI file:
```python
os.environ['GROQ_API_KEY'] = 'your_key_here'
```
- [ ] Reload web app

---

## 📝 Post-Deployment Tasks

### Update GitHub README:
- [ ] Add live demo link to README.md
- [ ] Add badge: `![Deployed](https://img.shields.io/badge/Deployed-PythonAnywhere-blue)`
- [ ] Push changes to GitHub

### Test All Features:
- [ ] News articles loading
- [ ] AI summaries working (click "Get AI Summary")
- [ ] Market sentiment analysis
- [ ] Predictions functionality
- [ ] Search and filters
- [ ] API endpoints responding

### Share Your Project:
- [ ] Add to LinkedIn profile
- [ ] Add to portfolio website
- [ ] Share on Twitter/social media
- [ ] Add to resume

---

## 📊 Important Information to Save

**Your Deployment Details:**

```
Username: _________________
App URL: https://__________.pythonanywhere.com
Dashboard: https://www.pythonanywhere.com/user/__________/
GitHub Repo: https://github.com/adrifayin/ai_news_intelligence

API Keys Used:
✓ Groq API
✓ NewsData.io API  
✓ OpenWeather API (optional)

Deployment Date: __________
Python Version: 3.10
Web Framework: FastAPI
Database: SQLite
```

---

## 🔄 Updating Your App

When you push changes to GitHub:

- [ ] SSH into Bash console
- [ ] Run: `cd ~/ai_news_intelligence`
- [ ] Run: `git pull origin main`
- [ ] If `requirements.txt` changed: `pip3.10 install --user -r requirements.txt`
- [ ] Web tab → Click "Reload"

---

## 📈 Monitoring

**Daily Checks:**
- [ ] Visit your app URL - ensure it's loading
- [ ] Check Web tab → Error log for issues
- [ ] Monitor CPU usage (Dashboard)

**Weekly Tasks:**
- [ ] Check API usage (Groq, NewsData, OpenWeather)
- [ ] Review server logs for unusual activity
- [ ] Backup database:
```bash
cd ~/ai_news_intelligence/backend
cp news_intelligence.db news_intelligence.db.backup
```

---

## 🎉 Success Criteria

All these should be ✅:

- [ ] App is accessible at your PythonAnywhere URL
- [ ] Homepage loads with no errors
- [ ] API documentation is available at `/docs`
- [ ] All pages (home, market, predictions) work
- [ ] No errors in error log
- [ ] Static files (CSS, JS) loading correctly
- [ ] Database is initialized and working
- [ ] API keys are configured
- [ ] News articles can be fetched
- [ ] AI features working (with Groq API)

---

## 🆘 Get Help

If stuck:
1. ✅ Check this checklist again
2. ✅ Read `PYTHONANYWHERE_DEPLOY.md` for detailed instructions
3. ✅ Check PythonAnywhere error logs
4. ✅ Search PythonAnywhere help: https://help.pythonanywhere.com/
5. ✅ Post on forums: https://www.pythonanywhere.com/forums/

---

## 🎊 Congratulations!

Once all boxes are checked, your DataStraw AI News Intelligence Platform is:

✅ **Live on the internet** (accessible worldwide)  
✅ **100% FREE forever** (no expiration)  
✅ **Professionally hosted** (HTTPS, monitoring, logs)  
✅ **Always available** (never sleeps)

**Time to celebrate!** 🥳

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-05-11  
**Total Time:** ~20 minutes (including verification)
