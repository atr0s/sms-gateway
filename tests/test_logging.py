import pytest
from pathlib import Path
import json
import logging

from sms_gateway.common.logging import get_logger, LOG_LEVELS
from sms_gateway.config import load_config
from sms_gateway.domain.models import SMSGatewayConfig, RuntimeConfig

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