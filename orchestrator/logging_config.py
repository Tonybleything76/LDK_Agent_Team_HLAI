"""
Centralized logging configuration for the LD Course Factory orchestrator.

Usage:
    from orchestrator.logging_config import get_logger
    logger = get_logger(__name__)

Log levels respect the LOG_LEVEL environment variable (default: INFO).
Structured JSON logging is enabled when LOG_FORMAT=json (useful in CI/CD).
"""

import logging
import os
import sys
from typing import Any, Dict


def _build_formatter() -> logging.Formatter:
    fmt = os.environ.get("LOG_FORMAT", "text").lower()
    if fmt == "json":
        try:
            import json as _json

            class _JsonFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:
                    payload: Dict[str, Any] = {
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                        "time": self.formatTime(record, self.datefmt),
                    }
                    if record.exc_info:
                        payload["exception"] = self.formatException(record.exc_info)
                    return _json.dumps(payload)

            return _JsonFormatter()
        except Exception:
            pass  # Fall back to text

    return logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def configure_logging() -> None:
    """
    Configure root logger once at application startup.

    Call this once from your entry point (``scripts/run_pipeline.py``,
    ``app.py``, etc.) before any other logging calls.
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        return  # Already configured — skip

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_build_formatter())
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, initialising logging if needed."""
    configure_logging()
    return logging.getLogger(name)
