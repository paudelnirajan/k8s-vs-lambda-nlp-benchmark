"""
Centralized logging configuration for the NLP service.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Default log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist


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
    # Default format: timestamp, logger name, level, message
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s'
        )
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times (important for Lambda)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)

    # Create console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler (if enabled)
    if log_to_file:
        # Determine log file path
        if log_file_path is None:
            # Use module name as log file name
            log_filename = f"{name.replace('.', '_')}.log"
            log_file_path = LOG_DIR / log_filename
        else:
            log_file_path = Path(log_file_path)
            # Ensure parent directory exists
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        # This automatically rotates logs when they reach max_bytes
        file_handler = RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file_path}")

    # Prevent propagation to root logger (optional, but cleaner)
    logger.propagate = False

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger with default configuration.
    This is a convenience function that modules can use.
    
    Args:
        name: Logger name (defaults to calling module's __name__)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name=name)