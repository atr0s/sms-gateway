from typing import Protocol, List
from sms_gateway.domain.models import Message
from sms_gateway.integrations.services.telegram.config import TelegramConfig
from sms_gateway.ports.messaging import MessagingPort

class TelegramPort(MessagingPort, Protocol):
    """Protocol for Telegram messaging"""
    
    async def initialize(self, config: TelegramConfig) -> None:
        """
        Initialize the Telegram service with bot config
        
        Args:
            config: Telegram bot configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
            TelegramError: If bot initialization fails
        """
        ...

    async def get_chat_info(self, chat_id: str) -> dict[str, str]:
        """
        Get information about a Telegram chat
        
        Args:
            chat_id: Telegram chat identifier
            
        Returns:
            Dictionary containing chat details (type, title, etc)
            
        Raises:
            TelegramError: If fetching chat info fails
            ChatNotFoundError: If chat doesn't exist
        """
        ...
        
    async def list_chats(self) -> List[dict[str, str]]:
        """
        List all available chats for the bot
        
        Returns:
            List of dictionaries containing chat details
            
        Raises:
            TelegramError: If fetching chats fails
        """
        ...

    async def send_file(self, chat_id: str, file_path: str, caption: str | None = None) -> None:
        """
        Send a file to a Telegram chat
        
        Args:
            chat_id: Telegram chat identifier
            file_path: Path to the file to send
            caption: Optional caption for the file
            
        Raises:
            TelegramError: If sending fails
            FileNotFoundError: If file doesn't exist
        """
        ...