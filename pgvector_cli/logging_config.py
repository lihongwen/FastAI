"""Logging configuration for pgvector CLI."""

import logging
import logging.config
import sys
from typing import Any, Dict

from .config import get_settings


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on settings."""
    settings = get_settings()

    log_level = "DEBUG" if settings.debug else "INFO"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s: %(message)s"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": sys.stderr
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "pgvector_cli.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "pgvector_cli": {
                "level": log_level,
                "handlers": ["console"] if not settings.debug else ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"]
        }
    }

    return config


def setup_logging():
    """Setup logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with consistent configuration."""
    return logging.getLogger(f"pgvector_cli.{name}")


class StructuredLogger:
    """Structured logger for better log analysis."""

    def __init__(self, name: str):
        self.logger = get_logger(name)

    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.info(full_message)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.warning(full_message)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with structured data."""
        # 分离标准logging参数和自定义字段
        logging_kwargs = {'exc_info': exc_info}

        # 处理自定义字段
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {extra_info}" if extra_info else message

        self.logger.error(full_message, **logging_kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.debug(full_message)
