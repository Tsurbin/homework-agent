from loguru import logger
from pathlib import Path
import sys

LOG_DIR = Path(__file__).resolve().parents[1]/"logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(LOG_DIR/"scraper.log", level="INFO", rotation="1 MB", retention=10)
