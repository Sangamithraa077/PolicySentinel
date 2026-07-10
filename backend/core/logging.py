"""Application-wide logging configuration.

Wires stdlib logging to a console handler and a rotating file handler.
Called once at process startup, before the FastAPI app is constructed.
"""

import logging.config
import os

from config.settings import Settings


def configure_logging(settings: Settings) -> None:
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.LOG_FILE_PATH,
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "default",
                "level": settings.LOG_LEVEL,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
        },
        "loggers": {
            "uvicorn": {"level": settings.LOG_LEVEL, "propagate": True},
            "uvicorn.access": {"level": settings.LOG_LEVEL, "propagate": True},
            "uvicorn.error": {"level": settings.LOG_LEVEL, "propagate": True},
        },
    }
    logging.config.dictConfig(logging_config)
