# 🚀 Deploy to Render.com

## Quick Setup Guide

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add render.yaml
   git commit -m "Add Render deployment config"
   git push
   ```

2. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables** (Optional)
   - Go to your service → Environment
   - Add:
     - `MONGO_URL` (if using MongoDB)
     - `DB_NAME` (if using MongoDB)
     - `CORS_ORIGINS` (your frontend URL)

4. **Deploy!**
   - Render will automatically deploy

---

### Option 2: Manual Setup

#### Step 1: Create New Web Service

1. Go to: https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your Git repository

#### Step 2: Configure Service

**Basic Settings:**
- **Name:** `pothos-backend` (or your choice)
- **Region:** Choose closest to your users
- **Branch:** `main` (or your default branch)
- **Root Directory:** `backend` ⚠️ **IMPORTANT**

**Build & Deploy:**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Advanced Settings:**
- **Python Version:** `3.11.0` (or check `api/runtime.txt`)

#### Step 3: Environment Variables (Optional)

Add these in the Environment tab:

| Key | Value | Required? |
|-----|-------|-----------|
| `MONGO_URL` | `mongodb+srv://...` | No |
| `DB_NAME` | `truedata` | No |
| `CORS_ORIGINS` | `https://your-frontend.com` | No (defaults to `*`) |

#### Step 4: Deploy

Click "Create Web Service" and wait for deployment!

---

## 📋 Configuration Summary

### Root Directory
```
backend
```
**Why:** Your `server.py` is in the `backend/` directory

### Build Command
```bash
pip install -r requirements.txt
```
**Why:** Installs all Python dependencies

### Start Command
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```
**Why:** 
- `uvicorn` is the ASGI server for FastAPI
- `server:app` means import `app` from `server.py`
- `--host 0.0.0.0` allows external connections
- `--port $PORT` uses Render's assigned port

### Python Version
```
3.11.0
```
**Why:** Matches your `api/runtime.txt`

---

## 🔍 Troubleshooting

### Issue: "Module not found"
**Fix:** Ensure `backend/requirements.txt` includes all dependencies

### Issue: "Port already in use"
**Fix:** Make sure start command uses `$PORT` (Render's variable)

### Issue: "Cannot find server.py"
**Fix:** Check Root Directory is set to `backend`

### Issue: "Build fails"
**Fix:** Check build logs - might be missing dependency in `requirements.txt`

---

## ✅ Verification

After deployment:

1. **Check Health Endpoint:**
   ```
   https://your-service.onrender.com/api/health
   ```
   Should return: `{"status": "ok", "message": "API is running"}`

2. **Check Root Endpoint:**
   ```
   https://your-service.onrender.com/api/
   ```
   Should return: `{"message": "TrueData Analytics API"}`

3. **Check Logs:**
   - Go to Render Dashboard → Your Service → Logs
   - Look for: `Application startup complete`

---

## 🎯 Key Differences from Vercel

| Aspect | Vercel | Render |
|--------|--------|--------|
| **Type** | Serverless Functions | Web Service |
| **Entry Point** | `api/index.py` | `backend/server.py` |
| **Server** | Mangum (Lambda adapter) | Uvicorn (ASGI server) |
| **Root Dir** | Project root | `backend/` |
| **Start Command** | Not needed | `uvicorn server:app ...` |

---

## 📝 Notes

1. **Root Directory:** Must be `backend` (not project root)
2. **Start Command:** Must use `$PORT` (Render's environment variable)
3. **No Mangum Needed:** Render runs uvicorn directly (no Lambda adapter)
4. **Environment Variables:** All optional - app works without them

---

## 🚀 Quick Deploy

```bash
# 1. Commit render.yaml
git add render.yaml RENDER_DEPLOY.md
git commit -m "Add Render deployment configuration"
git push

# 2. Go to Render Dashboard
# 3. Create new Web Service from repository
# 4. Use render.yaml or manual config above
# 5. Deploy!
```

Your backend will be live at: `https://your-service.onrender.com`

