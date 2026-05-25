# utils/helpers.py
import time
import uuid
from datetime import datetime, timezone

def generate_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:12]}"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def elapsed_seconds(start: float) -> float:
    return round(time.time() - start, 3)