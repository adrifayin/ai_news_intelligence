# 🔧 Vercel Configuration Fix

## The Issue
Vercel was showing 404 NOT_FOUND because it couldn't find the files in the `frontend/` subdirectory.

## ✅ What's Been Fixed

1. **Updated vercel.json** - Added proper routes to serve from `frontend/`
2. **Fixed HTML paths** - Changed `/static/style.css` to `style.css` (relative paths)
3. **Added page routes** - Proper routing for `/market` and `/predictions`

## 🚀 Vercel Dashboard Configuration

When deploying on Vercel, use these exact settings:

### Build & Development Settings

```
Framework Preset: Other (or blank)
Root Directory: frontend
Build Command: (leave empty)
Output Directory: (leave empty - serves root)
Install Command: (leave empty)
```

**IMPORTANT:** Set `Root Directory` to `frontend` - this tells Vercel where your files are!

### Or Use Override Option

If you already deployed, go to:
1. Project Settings → General
2. Scroll to "Root Directory"
3. Click "Edit"
4. Set to: `frontend`
5. Click "Save"
6. Redeploy

## 📝 Alternative: Deploy from Command Line

```bash
cd "C:\Users\ADHIL\Desktop\PROJECTS\DATA STRAW AI-Powered News Intelligence Platform"

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy with root directory
vercel --prod --cwd frontend
```

## ✅ Verify Deployment

After redeploying with correct root directory:

1. Visit your Vercel URL
2. Should see the homepage
3. Check `/market` page
4. Check `/predictions` page
5. Verify no 404 errors

## 🔗 Update Backend URL

Don't forget to update `vercel.json` with your Render backend URL:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://YOUR-ACTUAL-RENDER-APP.onrender.com/api/$1"
    }
  ]
}
```

Replace `YOUR-ACTUAL-RENDER-APP` with your Render service name.

## 🎯 Full Working Configuration

Your `vercel.json` should look like this:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-render-app.onrender.com/api/$1"
    }
  ],
  "routes": [
    {
      "src": "/market",
      "dest": "/frontend/market.html"
    },
    {
      "src": "/predictions",
      "dest": "/frontend/predictions.html"
    },
    {
      "src": "/(.*\\.(css|js|html))",
      "dest": "/frontend/$1"
    },
    {
      "src": "/",
      "dest": "/frontend/index.html"
    }
  ]
}
```

**BUT** if you set `Root Directory: frontend` in Vercel settings, the routes become simpler:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-render-app.onrender.com/api/$1"
    }
  ]
}
```

## 🎉 That's It!

Your Vercel deployment should now work correctly!

**Live URL:** `https://your-project.vercel.app`

All pages should load, and API calls will proxy to your Render backend.
