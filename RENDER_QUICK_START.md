# ⚡ Render.com Quick Start

## 🎯 Quick Answer

### Root Directory
```
backend
```

### Build Command
```
pip install -r requirements.txt
```

### Start Command
```
uvicorn server:app --host 0.0.0.0 --port $PORT
```

**OR** (if using start script):
```
./start.sh
```

---

## 📋 Step-by-Step Setup

### 1. Go to Render Dashboard
https://dashboard.render.com

### 2. Create New Web Service
- Click "New +" → "Web Service"
- Connect your Git repository

### 3. Configure Settings

**Basic:**
- **Name:** `pothos-backend`
- **Root Directory:** `backend` ⚠️ **IMPORTANT**
- **Branch:** `main`

**Build:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Advanced:**
- **Python Version:** `3.11.0`

### 4. Environment Variables (Optional)
- `MONGO_URL` - MongoDB connection (optional)
- `DB_NAME` - Database name (optional)
- `CORS_ORIGINS` - CORS origins (optional, defaults to `*`)

### 5. Deploy!
Click "Create Web Service"

---

## ✅ Verify Deployment

After deployment, test:

```
https://your-service.onrender.com/api/health
```

Should return: `{"status": "ok", "message": "API is running"}`

---

## 🔧 Alternative: Use render.yaml

If you pushed `render.yaml`, Render will auto-detect it:

1. Go to Render Dashboard
2. Click "New +" → "Blueprint"
3. Connect repository
4. Render will use `render.yaml` automatically!

---

## 📝 Summary

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Python Version** | `3.11.0` |

That's it! 🚀

