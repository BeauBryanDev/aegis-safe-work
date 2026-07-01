
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
 
from app.core.config import settings
 
 
# JSON formatter — structured logs for production (EC2 / CloudWatch)
 

class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.
    Includes standard fields plus any extra= kwargs passed to the logger call.
    """
 
    # Standard LogRecord attributes to exclude from the "extra" passthrough
    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "taskName",
    }
 
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
 
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
 
        # Pass through any extra={} fields passed to the log call
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
 
        return json.dumps(payload, default=str)
 
 
# Local Dev
class HumanFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        
# Setup — called once from main.py at startup


def setup_logging() -> None:
    """
    Configures the root logger. Call once at application startup,
    before any get_logger() calls produce output.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
 
    # Clear any pre-existing handlers (e.g. from uvicorn's default config)
    root.handlers.clear()
 
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(HumanFormatter() if settings.DEBUG else JSONFormatter())
    root.addHandler(handler)
 
    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )
    logging.getLogger("onnxruntime").setLevel(logging.WARNING)
 
 
def get_logger(name: str) -> logging.Logger:
    """
    Returns a module-scoped logger. Use __name__ as the argument so log
    output is traceable to the originating module.
 
    Example:
        logger = get_logger(__name__)
        logger.warning("Glove count exceeds cap", extra={"track_id": 3, "raw_count": 7})
    """
    return logging.getLogger(name)
 