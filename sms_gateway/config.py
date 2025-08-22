import json
import os
import logging
from pathlib import Path
from typing import Union
from pydantic import ValidationError

from sms_gateway.domain.models import SMSGatewayConfig
from sms_gateway.common.logging import get_logger, LOG_LEVELS

# Initialize with default level, will be updated after config load
logger = get_logger("config")

def _update_root_logger(config: SMSGatewayConfig) -> None:
    """Update root logger with configured log level"""
    # Initialize root logger first
    root_logger = get_logger("root")
    
    # Get the log level from config
    level = LOG_LEVELS.get(config.runtime.log_level.upper(), logging.INFO)
    
    # Set the root logger's level
    logging.getLogger().setLevel(level)
    logger.info(f"Set root logger level to {config.runtime.log_level}")

def load_config(config_path: Union[str, Path]) -> SMSGatewayConfig:
    """
    Load and validate gateway configuration from a JSON file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Validated SMSGatewayConfig instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid JSON
        ValidationError: If config is invalid according to schema
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    try:
        # Load JSON file
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        # Parse and validate config
        config = SMSGatewayConfig.model_validate(config_data)
        
        # Update logging level first
        _update_root_logger(config)
        
        logger.info(f"Loaded configuration from {config_path}")
        logger.debug(f"Config: {config.model_dump_json(indent=2)}")
        
        return config
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
        
    except ValidationError as e:
        logger.error("Configuration validation failed:")
        for error in e.errors():
            logger.error(f"- {' -> '.join(str(loc) for loc in error['loc'])}: {error['msg']}")
        raise
        
def get_default_config_path() -> Path:
    """
    Get the default configuration file path
    
    Returns:
        Path to default config file (./config.json)
    """
    return Path("config.json")