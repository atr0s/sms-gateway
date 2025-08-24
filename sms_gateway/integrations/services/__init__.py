"""SMS Gateway adapter registration.

This module ensures proper registration of all messaging adapters by importing
them in the correct order after the registry is initialized.
"""

# First import registry and types to ensure they're available
from sms_gateway.integrations.services.registry import AdapterRegistry, AdapterType

# Then import the adapters to trigger their registration decorators
from sms_gateway.integrations.services.stub_service.stub_service import StubSmsService
from sms_gateway.integrations.services.telegram.telegram import TelegramAdapter
from sms_gateway.integrations.services.gammu.gammu import GammuAdapter

# Register all available adapters and types
__all__ = [
    'AdapterRegistry',
    'AdapterType',
    'StubSmsService',
    'TelegramAdapter',
    'GammuAdapter'
]

# Get a list of registered adapters for debugging
sms_adapters = list(AdapterRegistry._adapters[AdapterType.SMS].keys())
integration_adapters = list(AdapterRegistry._adapters[AdapterType.INTEGRATION].keys())

from sms_gateway.common.logging import get_logger
logger = get_logger("adapters")
logger.info(f"Registered SMS adapters: {sms_adapters}")
logger.info(f"Registered integration adapters: {integration_adapters}")