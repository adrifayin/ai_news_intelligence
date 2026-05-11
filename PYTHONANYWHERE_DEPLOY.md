# 🚀 PythonAnywhere Deployment Guide - DataStraw

Complete step-by-step guide to deploy your DataStraw AI News Intelligence Platform on PythonAnywhere (100% FREE, Forever).

---

## 📋 What You'll Get

- ✅ **100% FREE** hosting (no credit card required)
- ✅ **Never sleeps** (unlike Render/Heroku)
- ✅ **Custom domain** support
- ✅ **HTTPS** included
- ✅ **512MB storage** + 100k API calls/day
- ✅ Your app at: `yourusername.pythonanywhere.com`

---

## 🎯 Prerequisites

- ✅ GitHub repo: https://github.com/adrifayin/ai_news_intelligence
- ✅ API Keys ready:
  - Groq API: https://console.groq.com
  - NewsData.io API: https://newsdata.io/api-keys
  - OpenWeather API: https://openweathermap.org/api

---

## 📝 Step 1: Sign Up for PythonAnywhere

1. **Go to:** https://www.pythonanywhere.com/registration/register/beginner/

2. **Create FREE account:**
   - Choose a username (this will be your URL: `username.pythonanywhere.com`)
   - Enter email and password
   - Verify email
   - No credit card required!

3. **Log in** to your dashboard

---

## 💻 Step 2: Clone Your Repository

1. **Open a Bash console:**
   - Dashboard → "Consoles" tab
   - Click "Bash" under "Start a new console"

2. **Clone your repository:**
```bash
git clone https://github.com/adrifayin/ai_news_intelligence.git
cd ai_news_intelligence
```

3. **Verify files:**
```bash
ls -la
# You should see: backend/, frontend/, requirements.txt, etc.
```

---

## 🔧 Step 3: Install Dependencies

In the same Bash console:

```bash
# Install Python packages (use --user flag)
pip3.10 install --user -r requirements.txt

# This takes 2-3 minutes
# You'll see installation progress for FastAPI, SQLAlchemy, etc.
```

**Important:** Always use `--user` flag on PythonAnywhere free tier.

---

## 📁 Step 4: Set Up Environment Variables

1. **Create .env file:**
```bash
cd ~/ai_news_intelligence
nano .env
```

2. **Add your API keys** (paste this and replace with your actual keys):
```env
# AI Processing
GROQ_API_KEY=gsk_your_groq_api_key_here

# News Data
NEWSDATA_API_KEY=pub_your_newsdata_api_key_here

# Weather (optional)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Database
DATABASE_URL=sqlite:///./news_intelligence.db

# JWT Secret (generate a random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# Environment
ENVIRONMENT=production
```

3. **Save and exit:**
   - Press `Ctrl + X`
   - Press `Y` to confirm
   - Press `Enter`

4. **Verify .env file:**
```bash
cat .env
# Make sure your keys are there
```

---

## 🌐 Step 5: Create Web App

1. **Go to "Web" tab** in PythonAnywhere dashboard

2. **Click "Add a new web app"**

3. **Choose:**
   - Click "Next" for your domain (`username.pythonanywhere.com`)
   - Select "Manual configuration" (NOT Flask/Django)
   - Choose **Python 3.10**
   - Click "Next"

4. **You'll see a success message** with your web app URL

---

## ⚙️ Step 6: Configure WSGI File

This is the **most important step** - it tells PythonAnywhere how to run your FastAPI app.

1. **On the Web tab, find "Code" section**

2. **Click on the WSGI configuration file link:**
   - It looks like: `/var/www/username_pythonanywhere_com_wsgi.py`

3. **Delete ALL existing content** and replace with this:

```python
"""
WSGI config for DataStraw FastAPI application on PythonAnywhere
"""

import sys
import os
from pathlib import Path

# Add your project directory to the sys.path
project_home = '/home/yourusername/ai_news_intelligence'  # ⚠️ CHANGE 'yourusername' to your actual username
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add backend directory to path
backend_path = os.path.join(project_home, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend
os.chdir(backend_path)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import FastAPI app
from main import app as application

# PythonAnywhere expects 'application' variable
# FastAPI app is already ASGI-compatible
```

4. **⚠️ IMPORTANT:** Replace `yourusername` with your actual PythonAnywhere username (line 11)

5. **Click "Save"** at the top

---

## 📂 Step 7: Configure Directories

Still on the **Web** tab:

### A. Source Code Directory
Find "Code" section:
```
Source code: /home/yourusername/ai_news_intelligence
```
Click "Edit" and enter your path (replace `yourusername`)

### B. Working Directory
```
Working directory: /home/yourusername/ai_news_intelligence/backend
```

### C. Static Files
Map your frontend files:

Click "Add a new static files mapping":

| URL | Directory |
|-----|-----------|
| `/` | `/home/yourusername/ai_news_intelligence/frontend` |
| `/static` | `/home/yourusername/ai_news_intelligence/frontend` |

*(Replace `yourusername` with your actual username)*

---

## 🔑 Step 8: Set Environment Variables (Alternative Method)

If `.env` file doesn't work, you can set variables in WSGI file directly:

Edit your WSGI file and add BEFORE the imports:

```python
# Set environment variables directly
os.environ['GROQ_API_KEY'] = 'your_key_here'
os.environ['NEWSDATA_API_KEY'] = 'your_key_here'
os.environ['OPENWEATHER_API_KEY'] = 'your_key_here'
os.environ['DATABASE_URL'] = 'sqlite:///./news_intelligence.db'
```

---

## 🎬 Step 9: Initialize Database

Back in your **Bash console**:

```bash
cd ~/ai_news_intelligence/backend
python3.10 -c "from database import init_db; init_db()"
```

This creates the SQLite database with all tables.

---

## 🚀 Step 10: Reload and Launch!

1. **Go back to "Web" tab**

2. **Click the big green "Reload" button** at the top

3. **Wait 10-15 seconds** for the app to start

4. **Visit your site:**
   - Click on your URL: `https://yourusername.pythonanywhere.com`
   - Or visit directly in browser

---

## ✅ Step 11: Verify Everything Works

### Test Homepage:
Visit: `https://yourusername.pythonanywhere.com/`
- Should see DataStraw dashboard

### Test API:
Visit: `https://yourusername.pythonanywhere.com/docs`
- Should see FastAPI Swagger documentation

### Test Endpoints:
```
✅ /api/articles - List articles
✅ /api/stats - Dashboard stats
✅ /api/markets/mood - Market sentiment
✅ /market - Market intelligence page
✅ /predictions - Predictions page
```

### Check for Errors:
- Web tab → "Log files" section
- Click "Error log" to see any issues
- Click "Server log" to see requests

---

## 🐛 Troubleshooting

### ❌ Problem: "Something went wrong" / 500 Error

**Solution 1: Check Error Log**
```
Web tab → Error log → Look for Python errors
```

Common errors and fixes:

**"No module named 'fastapi'"**
```bash
# Reinstall dependencies
cd ~/ai_news_intelligence
pip3.10 install --user -r requirements.txt
```

**"No module named 'backend'"**
- Check WSGI file has correct paths
- Verify `sys.path.insert(0, backend_path)` is present

**"Could not load application"**
- Check `from main import app as application` in WSGI
- Verify working directory is set to backend folder

---

### ❌ Problem: API Keys Not Working

**Solution:**
```bash
# Verify .env file exists
cd ~/ai_news_intelligence
cat .env

# If missing, recreate it
nano .env
# Add your keys and save
```

Or set them directly in WSGI file (see Step 8).

---

### ❌ Problem: Static Files (Frontend) Not Loading

**Solution:**
1. Web tab → Static files section
2. Verify mappings:
   - URL: `/` → Directory: `/home/yourusername/ai_news_intelligence/frontend`
3. Make sure files exist:
```bash
ls ~/ai_news_intelligence/frontend/
# Should see: index.html, app.js, style.css, etc.
```

---

### ❌ Problem: Database Errors

**Solution:**
```bash
# Recreate database
cd ~/ai_news_intelligence/backend
rm -f news_intelligence.db  # Delete old DB
python3.10 -c "from database import init_db; init_db()"
```

Then reload web app.

---

### ❌ Problem: App Runs Locally But Not on PythonAnywhere

**Check these:**

1. **Python version mismatch:**
   - Use Python 3.10 everywhere
   - Update any `python` commands to `python3.10`

2. **Path issues:**
   - Use absolute paths in WSGI file
   - Don't use relative imports like `from backend.main import app`
   - Use `from main import app` instead (since backend is in sys.path)

3. **WSGI configuration:**
   - Must have `application` variable (not `app`)
   - Must be ASGI-compatible (FastAPI is by default)

4. **File permissions:**
```bash
chmod -R 755 ~/ai_news_intelligence
```

---

## 🔄 Updating Your App

When you push changes to GitHub:

```bash
# SSH into PythonAnywhere console
cd ~/ai_news_intelligence
git pull origin main

# Reinstall dependencies if requirements.txt changed
pip3.10 install --user -r requirements.txt

# Reload web app
# Go to Web tab and click "Reload"
```

---

## 📊 Monitoring

### View Logs:
**Error Log:**
- Web tab → Error log
- Shows Python errors, exceptions

**Server Log:**
- Shows HTTP requests
- Useful for debugging API calls

**Access Log:**
- Shows all visitors
- IP addresses, user agents

### Check Resource Usage:
- Dashboard → CPU usage
- Free tier: 100 CPU-seconds/day
- Usually sufficient for small projects

---

## 🎯 Production Tips

### 1. Enable HTTPS (Already Included!)
PythonAnywhere provides HTTPS by default on `*.pythonanywhere.com` domains.

### 2. Custom Domain (Optional)
- Upgrade to paid plan ($5/month)
- Add your domain in Web tab
- Update DNS records

### 3. Database Backups
```bash
# Backup database
cd ~/ai_news_intelligence/backend
cp news_intelligence.db news_intelligence.db.backup

# Download backup
# Files tab → Navigate to file → Download
```

### 4. Schedule Tasks (Fetch News Automatically)
- Dashboard → "Tasks" tab
- Add scheduled task:
```bash
cd /home/yourusername/ai_news_intelligence/backend && python3.10 -c "from pipeline import run_pipeline; import asyncio; asyncio.run(run_pipeline())"
```
- Set frequency: Daily at 9:00 AM

### 5. Monitor API Usage
Check your API quotas:
- Groq: 30 requests/min (free)
- NewsData.io: 200 requests/day (free)
- OpenWeather: 1000 requests/day (free)

---

## 🎉 Success Checklist

- [ ] PythonAnywhere account created
- [ ] Repository cloned
- [ ] Dependencies installed
- [ ] .env file created with API keys
- [ ] Web app created
- [ ] WSGI file configured
- [ ] Static files mapped
- [ ] Database initialized
- [ ] App reloaded
- [ ] Homepage loads successfully
- [ ] API docs accessible at /docs
- [ ] No errors in error log
- [ ] Market page works
- [ ] Predictions page works

---

## 🆘 Still Having Issues?

### Check These Resources:

1. **PythonAnywhere Help:**
   - https://help.pythonanywhere.com/
   - Search for "FastAPI" or "ASGI"

2. **Forum:**
   - https://www.pythonanywhere.com/forums/

3. **Your Error Logs:**
   - Most issues are in the error log
   - Copy the error and search Google

4. **Test Locally First:**
```bash
# On your local machine
cd backend
python main.py
# Visit http://localhost:8000
```
If it works locally but not on PythonAnywhere, it's a configuration issue.

---

## 📈 Free Tier Limits

**What's Included (FREE):**
- 1 web app
- 512MB disk space
- 100,000 API calls/day
- 1 scheduled task
- Community support

**What's NOT Included:**
- Custom domains (need paid plan)
- SSH access (need paid plan)
- Multiple web apps
- Increased CPU quota

**For this project:** Free tier is MORE than enough! 🎉

---

## 🔗 Important URLs

After deployment, bookmark these:

- **Your App:** `https://yourusername.pythonanywhere.com`
- **API Docs:** `https://yourusername.pythonanywhere.com/docs`
- **Dashboard:** `https://www.pythonanywhere.com/user/yourusername/`
- **Web Tab:** `https://www.pythonanywhere.com/user/yourusername/webapps/`
- **Files:** `https://www.pythonanywhere.com/user/yourusername/files/`
- **Consoles:** `https://www.pythonanywhere.com/user/yourusername/consoles/`

---

## 🎊 You're Live!

Congratulations! Your DataStraw AI News Intelligence Platform is now:

✅ **Live on the internet** (accessible worldwide)  
✅ **100% FREE forever** (no credit card required)  
✅ **Never sleeps** (always available)  
✅ **Professionally hosted** (HTTPS, monitoring, logs)  

**Share your project:**
- Add to your resume/portfolio
- Share URL on LinkedIn
- Update GitHub README with live demo link

---

## 📧 Support

If you get stuck:
1. Check error logs first
2. Search PythonAnywhere help docs
3. Post on PythonAnywhere forums
4. Create GitHub issue on your repo

---

**Deployed with ❤️ using PythonAnywhere**

*Last updated: 2026-05-11*
