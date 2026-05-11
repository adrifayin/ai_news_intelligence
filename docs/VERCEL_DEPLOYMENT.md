# 🚀 Vercel Deployment Guide (Frontend)

Deploy the **frontend** of DataStraw to Vercel for free static hosting.

---

## 📋 Prerequisites

- GitHub account with the repository pushed
- Vercel account (sign up at https://vercel.com)
- Backend already deployed on Render (get the URL first)

---

## 🎯 Step-by-Step Deployment

### 1. Import Project to Vercel

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `adrifayin/ai_news_intelligence`
4. Click **"Import"**

### 2. Configure Build Settings

```
Framework Preset: Other
Root Directory: ./
Build Command: (leave empty)
Output Directory: frontend
Install Command: (leave empty)
```

### 3. Configure Environment Variables

**Important:** Add your Render backend URL

Click **"Environment Variables"** and add:

```
Name: VITE_API_URL
Value: https://your-app-name.onrender.com
```

Replace `your-app-name` with your actual Render app name.

### 4. Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes for deployment to complete
3. Your frontend will be live at: `https://your-project.vercel.app`

---

## 🔧 Update Backend URL in vercel.json

After getting your Render URL, update `vercel.json`:

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

Commit and push this change - Vercel will auto-redeploy.

---

## 🌐 Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as shown
4. SSL is automatic and free

---

## 🔄 Auto-Deployment

Vercel automatically redeploys when you push to GitHub:
- **Push to `main` branch** → Production deployment
- **Push to other branches** → Preview deployment

---

## ✅ Verify Deployment

After deployment, check:

1. **Frontend loads**: Visit your Vercel URL
2. **API connection works**: Check browser console for errors
3. **CORS is configured**: Backend should allow your Vercel domain

### Fix CORS Issues

If you see CORS errors, update your Render backend's CORS settings:

In `backend/main.py`, ensure CORS allows your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-project.vercel.app",  # Add your Vercel URL
        "*"  # Or use wildcard for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Vercel Dashboard Features

- **Deployments**: View all deployments and rollback if needed
- **Analytics**: Track page views and performance
- **Logs**: Real-time deployment and runtime logs
- **Preview Deployments**: Test changes before production

---

## 🐛 Troubleshooting

### Frontend loads but API calls fail

**Problem**: CORS errors or 404 on API calls

**Solution**:
1. Verify Render backend is running
2. Check `vercel.json` has correct Render URL
3. Update backend CORS to allow Vercel domain
4. Redeploy Render backend after CORS changes

### Deployment fails

**Problem**: Build errors

**Solution**:
- Ensure `frontend/` directory exists
- Check no build command is set (static site)
- Verify all HTML/CSS/JS files are in `frontend/`

### 404 on page refresh

**Problem**: SPA routing issues

**Solution**: Vercel handles this automatically with the `rewrites` in `vercel.json`

---

## 💰 Pricing

**Vercel Free Tier includes:**
- 100 GB bandwidth/month
- Unlimited static hosting
- Automatic SSL
- Global CDN
- Preview deployments

Perfect for this project! 🎉

---

## 🎉 Success!

Your frontend is now live on Vercel with auto-deployment from GitHub!

**Next Steps:**
1. Test all features on your live site
2. Share your URL: `https://your-project.vercel.app`
3. Monitor analytics in Vercel dashboard
4. Set up custom domain if desired

---

**Need help?** Check Vercel docs: https://vercel.com/docs
