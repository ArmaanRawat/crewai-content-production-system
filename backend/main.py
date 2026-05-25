"""
main.py
─────────────────────────────────────────────────────────────────
FastAPI application entry point.
─────────────────────────────────────────────────────────────────
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils.logger import setup_logging, get_logger
from api.routes import router

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "DEBUG"))
logger = get_logger(__name__)

app = FastAPI(
    title="CrewAI Content Production System",
    version="0.1.0",
)

# ── CORS — allows React frontend to talk to this API ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

logger.info("App started", host="0.0.0.0", port=8000)