"""
main.py
─────────────────────────────────────────────────────────────────
FastAPI application entry point.
─────────────────────────────────────────────────────────────────
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils.logger import setup_logging, get_logger
from api.routes import router
from api.feedback_routes import router as feedback_router
from api.translation_routes import router as translation_router
from api.calender_routes import router as calendar_router

load_dotenv()

# ── Silence noisy third-party debug loggers ───────────────────────────────────
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
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
app.include_router(feedback_router, prefix="/api/v1/feedback")
app.include_router(translation_router, prefix="/api/v1/translation")
app.include_router(calendar_router, prefix="/api/v1/calendar")


@app.on_event("startup")
def startup_event():
    """
    Runs on server startup.
    """
    logger.info("Server startup: auto-generating technical documentation")
    try:
        from utils.doc_generator import generate_docs
        generate_docs()
    except Exception as e:
        logger.error(f"Failed to auto-generate technical documentation: {e}")

    logger.info("App started", host="0.0.0.0", port=8000)