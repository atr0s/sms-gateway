from typing import Protocol, Iterator, Optional
from sms_gateway.domain.messaging import Message
from sms_gateway.integrations.config import BaseConfig

class MessagingPort(Protocol):
    """Base protocol for all messaging services"""
    name: str
    async def send_message(self, message: Message) -> None:
        """
        Send a message through this service
        
        Args:
            message: The message to send
            
        Raises:
            MessagingError: If sending fails
        """
        ...
        
    async def get_message(self) -> Optional[Message]:
        """
        Get a single message from this service
        
        Returns:
            A received message, or None if no messages are available
            
        Raises:
            MessagingError: If receiving fails
            RuntimeError: If service is not initialized
        """
        ...
        
    async def initialize(self, config: BaseConfig) -> None:
        """
        Initialize the messaging service with config
        
        Args:
            config: Service-specific configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        ...
        
    async def shutdown(self) -> None:
        """Cleanup and shutdown the service"""
        ...