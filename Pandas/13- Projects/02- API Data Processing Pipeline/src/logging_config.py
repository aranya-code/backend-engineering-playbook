from __future__ import annotations

import logging
from logging.config import dictConfig

from .config import PipelineConfig, config


def configure_logging(
    pipeline_config: PipelineConfig = config,
) -> logging.Logger:
    """Configure application logging and return the package logger."""
    level = pipeline_config.log_level.upper()

    if not hasattr(logging, level):
        raise ValueError(
            f"Unsupported log level: {pipeline_config.log_level}"
        )

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": pipeline_config.log_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "standard",
                    "stream": "ext://sys.stderr",
                },
            },
            "root": {
                "level": level,
                "handlers": ["console"],
            },
        }
    )

    return logging.getLogger("api_data_pipeline")


def get_logger(
    name: str | None = None,
) -> logging.Logger:
    """Return a named logger using the pipeline logger hierarchy."""
    logger_name = (
        f"api_data_pipeline.{name}"
        if name
        else "api_data_pipeline"
    )

    return logging.getLogger(logger_name)


__all__ = [
    "configure_logging",
    "get_logger",
]

from __future__ import annotations

import logging
from logging.config import dictConfig

from .config import PipelineConfig, config


def configure_logging(
    pipeline_config: PipelineConfig = config,
) -> logging.Logger:
    """Configure application logging and return the package logger."""
    level = pipeline_config.log_level.upper()

    if not hasattr(logging, level):
        raise ValueError(
            f"Unsupported log level: {pipeline_config.log_level}"
        )

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": pipeline_config.log_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "standard",
                    "stream": "ext://sys.stderr",
                },
            },
            "root": {
                "level": level,
                "handlers": ["console"],
            },
        }
    )

    return logging.getLogger("api_data_pipeline")


def get_logger(
    name: str | None = None,
) -> logging.Logger:
    """Return a named logger using the pipeline logger hierarchy."""
    logger_name = (
        f"api_data_pipeline.{name}"
        if name
        else "api_data_pipeline"
    )

    return logging.getLogger(logger_name)


__all__ = [
    "configure_logging",
    "get_logger",
]