import sys
import logging
import asyncio
import threading
from pathlib import Path
from loguru import logger as _logger

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Thread-safe SSE broadcaster registry
_listeners = set()
_lock = threading.Lock()

def register_listener(queue: asyncio.Queue):
    with _lock:
        _listeners.add(queue)

def unregister_listener(queue: asyncio.Queue):
    with _lock:
        _listeners.discard(queue)

def sse_sink(message):
    """
    Loguru sink that broadcasts log messages to all registered SSE queues.
    """
    record = message.record
    message_str = record['message']
    
    # Filter out polling HTTP requests from cluttering the live agent terminal
    if record['name'] == "uvicorn.access" or any(endpoint in message_str for endpoint in ["/api/v1/jobs", "/api/v1/health", "/api/v1/logs/stream"]):
        return
        
    # Clean formatting for web console
    formatted = f"{record['time'].strftime('%Y-%m-%d %H:%M:%S')} | {record['level'].name:8} | {record['name']}:{record['line']} - {message_str}\n"
    
    with _lock:
        for q in list(_listeners):
            try:
                loop = q._loop if hasattr(q, '_loop') else asyncio.get_event_loop()
                if loop and loop.is_running():
                    loop.call_soon_threadsafe(q.put_nowait, formatted)
            except Exception:
                pass

class InterceptHandler(logging.Handler):
    """
    Logs standard library logging messages (e.g. from CrewAI, Uvicorn) through Loguru.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        _logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging(log_level: str = "DEBUG") -> None:
    _logger.remove()
    
    # 1. Console stderr logger
    _logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )
    
    # 2. SSE broadcaster sink
    _logger.add(
        sse_sink,
        level=log_level,
        format="{message}"
    )
    
    # 3. Rotating file logger
    _logger.add(
        LOG_DIR / "app.log",
        rotation="10 MB",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}"
    )

    # Configure standard logging to redirect through InterceptHandler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Force uvicorn and crewai standard loggers to propagate to the root logger (intercepted by Loguru)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "crewai"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True

def get_logger(name: str):
    return _logger.bind(module=name)