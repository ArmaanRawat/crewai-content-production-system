import sys
from pathlib import Path
from loguru import logger as _logger

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logging(log_level: str = "DEBUG") -> None:
    _logger.remove()
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

def get_logger(name: str):
    return _logger.bind(module=name)