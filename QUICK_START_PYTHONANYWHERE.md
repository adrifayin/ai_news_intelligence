# ⚡ Quick Start - PythonAnywhere Deployment (10 Minutes)

Deploy DataStraw to PythonAnywhere in 10 minutes - 100% FREE forever!

---

## 🎯 Quick Overview

```
1. Sign up (2 min) → 2. Clone repo (1 min) → 3. Install deps (3 min) 
→ 4. Configure WSGI (2 min) → 5. Deploy (1 min) → 6. Done! 🎉
```

---

## 📝 Step-by-Step Commands

### 1️⃣ Sign Up (2 minutes)
- Go to: https://www.pythonanywhere.com/registration/register/beginner/
- Choose username (becomes your URL: `username.pythonanywhere.com`)
- Verify email, log in

---

### 2️⃣ Clone Repository (1 minute)
Dashboard → Consoles → Bash

```bash
git clone https://github.com/adrifayin/ai_news_intelligence.git
cd ai_news_intelligence
```

---

### 3️⃣ Install Dependencies (3 minutes)
```bash
pip3.10 install --user -r requirements.txt
```

Wait for installation to complete...

---

### 4️⃣ Create Environment File (2 minutes)
```bash
nano .env
```

Paste this (replace with YOUR API keys):
```env
GROQ_API_KEY=gsk_your_actual_groq_key_here
NEWSDATA_API_KEY=pub_your_actual_newsdata_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
DATABASE_URL=sqlite:///./news_intelligence.db
JWT_SECRET_KEY=change-this-to-random-string
ENVIRONMENT=production
```

Save: `Ctrl+X` → `Y` → `Enter`

---

### 5️⃣ Create Web App (2 minutes)

**Web Tab → "Add a new web app"**

1. Click "Next" (accept default URL)
2. Select **"Manual configuration"**
3. Choose **"Python 3.10"**
4. Click "Next"

---

### 6️⃣ Configure WSGI (3 minutes)

**Web Tab → WSGI configuration file** (click the link)

**DELETE everything** and paste this:

```python
import sys
import os

# ⚠️ CHANGE 'yourusername' to your actual PythonAnywhere username
project_home = '/home/yourusername/ai_news_intelligence'

# Add paths
sys.path.insert(0, project_home)
sys.path.insert(0, os.path.join(project_home, 'backend'))
os.chdir(os.path.join(project_home, 'backend'))

# Load environment
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import app
from main import app as application
```

**⚠️ IMPORTANT:** Replace `yourusername` with YOUR actual username!

Click **Save**

---

### 7️⃣ Configure Static Files (1 minute)

**Web Tab → Static files section**

Click "Enter URL" and add:

| URL | Directory |
|-----|-----------|
| `/` | `/home/yourusername/ai_news_intelligence/frontend` |

*(Replace `yourusername` with yours)*

---

### 8️⃣ Set Source Code Path (30 seconds)

**Web Tab → Code section**

```
Source code: /home/yourusername/ai_news_intelligence
Working directory: /home/yourusername/ai_news_intelligence/backend
```

*(Replace `yourusername` with yours)*

---

### 9️⃣ Initialize Database (1 minute)

Back to **Bash console**:

```bash
cd ~/ai_news_intelligence/backend
python3.10 -c "from database import init_db; init_db()"
```

---

### 🔟 Launch! (30 seconds)

**Web Tab → Click big green "Reload" button**

Wait 10 seconds...

**Visit your site:** `https://yourusername.pythonanywhere.com`

---

## ✅ Verify It Works

Test these URLs:

- **Homepage:** `https://yourusername.pythonanywhere.com/`
- **API Docs:** `https://yourusername.pythonanywhere.com/docs`
- **Market Page:** `https://yourusername.pythonanywhere.com/market`
- **Predictions:** `https://yourusername.pythonanywhere.com/predictions`

---

## 🐛 Quick Troubleshooting

### ❌ "Something went wrong"
**→** Web tab → Error log → Look for the error

### ❌ "No module named 'fastapi'"
```bash
cd ~/ai_news_intelligence
pip3.10 install --user -r requirements.txt
```
Then reload web app

### ❌ API keys not working
Check your `.env` file:
```bash
cat ~/ai_news_intelligence/.env
```

Or set them directly in WSGI file:
```python
os.environ['GROQ_API_KEY'] = 'your_key_here'
```

### ❌ Frontend not loading
- Web tab → Static files
- Verify path: `/home/yourusername/ai_news_intelligence/frontend`
- Make sure `yourusername` is YOUR username

---

## 🎉 Success!

Your DataStraw platform is now live and accessible worldwide!

**Free tier includes:**
- ✅ Never sleeps (always online)
- ✅ HTTPS included
- ✅ 100,000 API calls/day
- ✅ 512MB storage
- ✅ No credit card needed

---

## 📖 Need More Help?

See the full guide: `PYTHONANYWHERE_DEPLOY.md`

---

**Time to complete:** ~10 minutes  
**Cost:** $0 (FREE forever)  
**Difficulty:** Easy

Happy deploying! 🚀
