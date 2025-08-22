import logging
from typing import Optional, Union
from pathlib import Path

# Map string log levels to logging constants
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class Logger:
    """Logging abstraction that wraps Python's logging module"""
    
    def __init__(self, name: str, log_level: Union[str, int] = None):
        self.logger = logging.getLogger(name)
        
        # If no level specified, don't set one (will inherit from root)
        if log_level is not None:
            # Convert string level to int if needed
            if isinstance(log_level, str):
                level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
            else:
                level = log_level
            self.logger.setLevel(level)
        
        # Only set up handlers for root logger or if explicitly requested
        if name == "root" and not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup console and file handlers with formatting"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str) -> None:
        """Log debug message"""
        self.logger.debug(msg)
    
    def info(self, msg: str) -> None:
        """Log info message"""
        self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        """Log warning message"""
        self.logger.warning(msg)
    
    def error(self, msg: str) -> None:
        """Log error message"""
        self.logger.error(msg)
    
    def critical(self, msg: str) -> None:
        """Log critical message"""
        self.logger.critical(msg)
    
    def exception(self, msg: str) -> None:
        """Log exception message with traceback"""
        self.logger.exception(msg)

# Convenience function to get a logger instance
def get_logger(name: str) -> Logger:
    """Get a logger instance with the given name"""
    return Logger(name)