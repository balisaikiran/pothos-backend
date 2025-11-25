# 🔧 Fix: "Could not import module 'server'"

## The Problem

Render can't find `server.py` because the root directory or start command isn't configured correctly.

## ✅ Solution

### Option 1: Update Render Dashboard Settings

1. Go to your Render service dashboard
2. Click **"Settings"** tab
3. Scroll to **"Build & Deploy"** section
4. Update these settings:

**Root Directory:**
```
backend
```

**Build Command:**
```
pip install -r requirements.txt
```
(Note: No `backend/` prefix since root is `backend`)

**Start Command:**
```
uvicorn server:app --host 0.0.0.0 --port $PORT
```

5. **Save** and redeploy

---

### Option 2: Use Updated render.yaml

I've updated `render.yaml` with the correct `rootDir` setting. 

1. **Commit and push:**
   ```bash
   git add render.yaml
   git commit -m "Fix: Set rootDir in render.yaml"
   git push
   ```

2. **Redeploy on Render:**
   - Go to Render Dashboard
   - Your service should auto-redeploy
   - Or click "Manual Deploy" → "Deploy latest commit"

---

## 🔍 Why This Happened

The issue was:
- **Before:** Root directory wasn't explicitly set, so commands ran from project root
- **Build command:** `pip install -r backend/requirements.txt` (correct for project root)
- **Start command:** `cd backend && uvicorn server:app ...` (trying to change directory)

**Now:**
- **Root directory:** Set to `backend` explicitly
- **Build command:** `pip install -r requirements.txt` (no prefix needed)
- **Start command:** `uvicorn server:app ...` (runs from backend directory)

---

## ✅ Verify Fix

After redeploying, check:

1. **Build logs** should show:
   ```
   Installing dependencies from requirements.txt...
   ```

2. **Start logs** should show:
   ```
   INFO:     Started server process
   INFO:     Application startup complete.
   ```

3. **Test endpoint:**
   ```
   https://your-service.onrender.com/api/health
   ```
   Should return: `{"status": "ok", "message": "API is running"}`

---

## 📋 Correct Settings Summary

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Python Version** | `3.11.0` |

---

## 🚀 Quick Fix Steps

1. **Update render.yaml** (already done)
2. **Push to Git:**
   ```bash
   git add render.yaml
   git commit -m "Fix Render deployment - set rootDir"
   git push
   ```
3. **Redeploy on Render** (should auto-deploy)
4. **Check logs** - should work now!

---

## ⚠️ If Still Not Working

If you still see the error:

1. **Check Render Dashboard → Settings:**
   - Verify "Root Directory" is set to `backend`
   - Verify "Start Command" is exactly: `uvicorn server:app --host 0.0.0.0 --port $PORT`

2. **Check Build Logs:**
   - Should show dependencies installing
   - Should show `Successfully installed...`

3. **Check Start Logs:**
   - Look for any import errors
   - Should show `Application startup complete`

4. **Verify File Structure:**
   - `backend/server.py` exists
   - `backend/requirements.txt` exists

The fix should work now! 🎉








