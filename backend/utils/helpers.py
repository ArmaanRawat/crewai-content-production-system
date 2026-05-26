# utils/helpers.py
import os
import time
import uuid
from datetime import datetime, timezone
from crewai import LLM

def generate_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:12]}"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def elapsed_seconds(start: float) -> float:
    return round(time.time() - start, 3)

def get_llm():
    """
    Load the LLM configuration dynamically based on the environment variables.
    Supports native Gemini or OpenAI-compatible endpoints (e.g. OpenRouter).
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip():
        return "gemini/gemini-2.0-flash-lite"
        
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.strip():
        openai_model = os.getenv("OPENAI_MODEL", "deepseek/deepseek-chat")
        openai_base = os.getenv("OPENAI_API_BASE")
        
        # If using OpenRouter, ensure model is prefixed with 'openrouter/'
        # so LiteLLM doesn't strip the provider prefix (e.g. 'deepseek/')
        if openai_base and "openrouter.ai" in openai_base.lower():
            if not openai_model.startswith("openrouter/"):
                openai_model = f"openrouter/{openai_model}"
                
        return LLM(
            model=openai_model,
            base_url=openai_base,
            api_key=openai_key
        )
        
    return "gpt-4o"