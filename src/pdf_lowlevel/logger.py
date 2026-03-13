"""
Logging configuration for pdf-lowlevel.

Uses loguru for structured, colorful logging.
"""

import sys
from typing import Optional

from loguru import logger

# Remove default handler
logger.remove()

# Add custom handler with appropriate format
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Export the configured logger
__all__ = ["logger", "configure_logger"]


def configure_logger(
    level: str = "INFO",
    format: Optional[str] = None,
    sink: Optional[str] = None,
) -> None:
    """
    Configure the logger with custom settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Custom format string (optional)
        sink: Output sink - file path for file logging, None for stderr
    """
    logger.remove()

    if format is None:
        format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    if sink:
        # Log to file
        logger.add(sink, format=format, level=level, rotation="10 MB")
    else:
        # Log to stderr
        logger.add(sys.stderr, format=format, level=level, colorize=True)