import pytest
from pathlib import Path
import json
import logging

from sms_gateway.common.logging import get_logger, LOG_LEVELS
from sms_gateway.config import load_config

def test_default_log_level(tmp_path):
    """Test that log level defaults to INFO when not specified"""
    # Create minimal config
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "name": "test-gateway",
            "sms": {},
            "integration": {},
            "queues": {
                "sms_queue": {"type": "memory"},
                "integration_queue": {"type": "memory"}
            }
        }, f)
    
    # Load config and verify log level
    config = load_config(config_path)
    assert config.runtime.log_level == "INFO"
    
    # Verify logger level
    logger = get_logger("test")
    assert logger.logger.getEffectiveLevel() == logging.INFO

def test_custom_log_level(tmp_path):
    """Test that custom log level is applied correctly"""
    # Create config with DEBUG level
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "name": "test-gateway",
            "sms": {},
            "integration": {},
            "queues": {
                "sms_queue": {"type": "memory"},
                "integration_queue": {"type": "memory"}
            },
            "runtime": {
                "log_level": "DEBUG"
            }
        }, f)
    
    # Load config and verify log level
    config = load_config(config_path)
    assert config.runtime.log_level == "DEBUG"
    
    # Verify logger level
    logger = get_logger("test")
    assert logger.logger.getEffectiveLevel() == logging.DEBUG

def test_invalid_log_level(tmp_path):
    """Test that invalid log level falls back to INFO"""
    # Create config with invalid level
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "name": "test-gateway",
            "sms": {},
            "integration": {},
            "queues": {
                "sms_queue": {"type": "memory"},
                "integration_queue": {"type": "memory"}
            },
            "runtime": {
                "log_level": "INVALID"
            }
        }, f)
    
    # Load config and verify log level falls back to INFO
    config = load_config(config_path)
    logger = get_logger("test")
    assert logger.logger.getEffectiveLevel() == logging.INFO

def test_component_specific_logging(tmp_path):
    """Test that component-specific logging levels are applied correctly"""
    # Create config with component-specific levels
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "name": "test-gateway",
            "sms": {},
            "integration": {},
            "queues": {
                "sms_queue": {"type": "memory"},
                "integration_queue": {"type": "memory"}
            },
            "runtime": {
                "logging": {
                    "default": "INFO",
                    "components": {
                        "httpx": "WARNING",
                        "sms_gateway.services": "DEBUG"
                    }
                }
            }
        }, f)
    
    # Load config and verify component levels
    config = load_config(config_path)
    
    # Verify default level is applied
    root_logger = logging.getLogger()
    assert root_logger.getEffectiveLevel() == logging.INFO
    
    # Verify component levels are applied
    httpx_logger = logging.getLogger("httpx")
    assert httpx_logger.getEffectiveLevel() == logging.WARNING
    
    services_logger = logging.getLogger("sms_gateway.services")
    assert services_logger.getEffectiveLevel() == logging.DEBUG
    
    # Verify other loggers inherit default
    other_logger = get_logger("other")
    assert other_logger.logger.getEffectiveLevel() == logging.INFO

def test_backwards_compatibility(tmp_path):
    """Test that old log_level setting still works when no components defined"""
    # Create config with old log_level
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump({
            "name": "test-gateway",
            "sms": {},
            "integration": {},
            "queues": {
                "sms_queue": {"type": "memory"},
                "integration_queue": {"type": "memory"}
            },
            "runtime": {
                "log_level": "DEBUG"
            }
        }, f)
    
    # Load config and verify level is applied
    config = load_config(config_path)
    
    # Should use log_level since no components defined
    root_logger = logging.getLogger()
    assert root_logger.getEffectiveLevel() == logging.DEBUG
    
    # All loggers should inherit DEBUG level
    test_logger = get_logger("test")
    assert test_logger.logger.getEffectiveLevel() == logging.DEBUG