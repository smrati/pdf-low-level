"""
Logging configuration for pdf-lowlevel.

Uses Python's native logging module with colorful output.
"""

import logging
import sys
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for log formatting."""
    GREEN = '\033[32m'
    CYAN = '\033[36m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD_RED = '\033[1;31m'
    RESET = '\033[0m'

    # Level-specific colors
    LEVEL_COLORS = {
        'DEBUG': CYAN,
        'INFO': GREEN,
        'WARNING': YELLOW,
        'ERROR': RED,
        'CRITICAL': BOLD_RED,
    }


class ColorfulFormatter(logging.Formatter):
    """Custom formatter with colorful output mimicking loguru style."""

    def format(self, record):
        # Get color for level
        level_color = Colors.LEVEL_COLORS.get(record.levelname, Colors.RESET)
        
        # Format timestamp
        asctime = self.formatTime(record, self.datefmt)
        
        # Build the formatted message with colors
        formatted = (
            f"{Colors.GREEN}{asctime}{Colors.RESET} | "
            f"{level_color}{record.levelname:<8}{Colors.RESET} | "
            f"{Colors.CYAN}{record.name}{Colors.RESET}:"
            f"{Colors.CYAN}{record.funcName}{Colors.RESET}:"
            f"{Colors.CYAN}{record.lineno}{Colors.RESET} - "
            f"{level_color}{record.getMessage()}{Colors.RESET}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted


class PlainFormatter(logging.Formatter):
    """Plain formatter without colors for file output."""

    def format(self, record):
        # Format timestamp
        asctime = self.formatTime(record, self.datefmt)
        
        # Build the formatted message
        formatted = (
            f"{asctime} | "
            f"{record.levelname:<8} | "
            f"{record.name}:{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted


# Create the logger instance
logger = logging.getLogger('pdf_lowlevel')
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Don't propagate to root logger

# Export the configure function
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
        format: Custom format string (optional, ignored - kept for API compatibility)
        sink: Output sink - file path for file logging, None for stderr
    """
    # Clear existing handlers
    logger.handlers.clear()
    
    # Convert level string to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create appropriate handler
    if sink:
        # Log to file (no colors)
        handler = logging.FileHandler(sink, encoding='utf-8')
        handler.setFormatter(PlainFormatter(datefmt='%Y-%m-%d %H:%M:%S'))
    else:
        # Log to stderr with colors
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(ColorfulFormatter(datefmt='%Y-%m-%d %H:%M:%S'))
    
    handler.setLevel(log_level)
    logger.addHandler(handler)


# Configure default logging on import
configure_logger()