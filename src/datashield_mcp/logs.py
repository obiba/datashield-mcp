# Create log directory if it doesn't exist
# Try current folder first, fall back to home if not writable
import logging
import sys
from pathlib import Path


log_dir = Path.cwd() / ".datashield" / "logs"
try:
    log_dir.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    log_dir = Path.home() / ".datashield" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

# Configure logging to file and stderr
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "mcp.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger(__name__)
