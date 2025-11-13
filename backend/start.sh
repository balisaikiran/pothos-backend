#!/bin/bash
# Start script for Render.com
# This script starts the FastAPI server using uvicorn

# Get port from environment variable (Render provides this)
PORT=${PORT:-8000}

# Start uvicorn server
exec uvicorn server:app --host 0.0.0.0 --port $PORT

