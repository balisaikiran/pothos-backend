# Environment Variables Guide

## ✅ Good News: NO Environment Variables Required!

Your backend is designed to work **WITHOUT any environment variables**. They are all optional.

## 📋 Optional Environment Variables

### 1. `MONGO_URL` (Optional)
- **Purpose:** MongoDB connection string for storing login tokens
- **Default:** None (app works without it)
- **When to set:** If you want to store tokens in MongoDB
- **Example:** `mongodb+srv://user:pass@cluster.mongodb.net/`

### 2. `DB_NAME` (Optional)
- **Purpose:** MongoDB database name
- **Default:** None (app works without it)
- **When to set:** If using MongoDB
- **Example:** `truedata`

### 3. `CORS_ORIGINS` (Optional)
- **Purpose:** Allowed CORS origins (comma-separated)
- **Default:** `*` (allows all origins)
- **When to set:** To restrict CORS for security
- **Example:** `https://your-app.vercel.app,https://www.your-app.vercel.app`

## 🚀 For Vercel Deployment

### Minimum Setup (No Env Vars Needed)
Your app will work with **ZERO environment variables**!

### Recommended Setup (For Production)
Set these in Vercel Dashboard → Settings → Environment Variables:

```
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=truedata
CORS_ORIGINS=https://your-app.vercel.app
```

## ⚠️ Important Notes

1. **App works without MongoDB** - Tokens will be stored in frontend localStorage instead
2. **CORS defaults to `*`** - Allows all origins if not set
3. **No env vars = app still works** - Just with limited features

## 🔍 If Function Still Fails

The issue is **NOT** environment variables. Check:

1. **Vercel Function Logs** - Will show the actual error
2. **Dependencies** - Ensure `api/requirements.txt` has all packages
3. **File Structure** - Ensure `backend/server.py` exists
4. **Python Version** - Check `api/runtime.txt`

The function should work even with zero environment variables!

