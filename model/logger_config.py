"""
Centralized logging configuration for the NLP service.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

# Default log directory - only create when needed, not at import time
def get_log_dir():
    """Get log directory, creating it only if not in Lambda."""
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        # In Lambda, use /tmp if we need file logging (but we won't)
        return Path("/tmp")
    else:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        return log_dir


def setup_logger(
    name: str = "nlp_inference",
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_to_file: bool = True,
    log_file_path: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB per file
    backup_count: int = 5  # Keep 5 backup files
) -> logging.Logger:
    """
    Setup and return a configured logger with both console and file handlers.

    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string. If None, uses defaults.
        log_to_file: Whether to log to file (default: True)
        log_file_path: Custom path for log file. If None, uses default location.
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    
    Returns:
        Configured logger instance
    """
    # Auto-detect Lambda environment and disable file logging
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        log_to_file = False
    
    # Default format: timestamp, logger name, level, message
    file_format = (
        '%(asctime)s | %(levelname)-8s | %(name)-20s | '
        '%(filename)s:%(lineno)-4d | %(message)s'
    )

    if HAS_COLORLOG:
        console_format = (
            '%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-20s | '
            '%(filename)s:%(lineno)-4d | %(message)s'
        )
        colors = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    else:
        console_format = file_format
        colors = None

    # Use custom format if provided
    if format_string:
        file_format = format_string
        console_format = format_string
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times (important for Lambda)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    
    # Create console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if HAS_COLORLOG and not format_string:
        console_formatter = colorlog.ColoredFormatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors=colors,
            reset=True,
            style='%'
        )
    else:
        console_formatter = logging.Formatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
        
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler (if enabled)
    if log_to_file:
        # Determine log file path
        if log_file_path is None:
            log_filename = f"{name.replace('.', '_')}.log"
            log_file_path = get_log_dir() / log_filename
        else:
            log_file_path = Path(log_file_path)
            if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        # Use clean file format
        file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file_path}")

    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with default configuration.
    This is a convenience function that modules can use.
    
    Args:
        name: Logger name (defaults to 'nlp_inference' if not provided)
        
    Returns:
        Configured logger instance
    """
    if name is None:
        name = "nlp_inference"
    return setup_logger(name=name)