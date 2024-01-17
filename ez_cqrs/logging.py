"""Logging module."""
from __future__ import annotations

import os
import sys
from functools import cache

import loguru


@cache
def _configure_logger(logger: loguru.Logger, level: str) -> loguru.Logger:
    """Configure logger for the system."""
    logger.remove()
    fmt = "{time:HH:mm:ss} <lvl>[{level}]</lvl> {message} <green>{name}:{function}:{line}</green>"
    logger.add(sys.stderr, format=fmt, level=level)
    return logger


logger = _configure_logger(logger=loguru.logger, level=os.environ["LOG_LEVEL"])
