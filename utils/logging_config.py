"""
Logging Configuration
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from .config import config


def setup_logging():
    """Setup application logging"""
    
    # Create logger
    logger = logging.getLogger("recruitment_ai")
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized - Level: {config.LOG_LEVEL}")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    return logger


# Initialize logging
logger = setup_logging()
