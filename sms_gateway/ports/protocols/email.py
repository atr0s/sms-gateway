from typing import Protocol, List
from sms_gateway.domain.models import Message, EmailConfig
from sms_gateway.ports.messaging import MessagingPort

class EmailPort(MessagingPort, Protocol):
    """Protocol for Email messaging"""
    
    async def initialize(self, config: EmailConfig) -> None:
        """
        Initialize the Email service with SMTP config
        
        Args:
            config: SMTP server configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
            SMTPError: If server connection fails
        """
        ...

    async def send_with_attachment(
        self, 
        message: Message, 
        attachments: List[str]
    ) -> None:
        """
        Send an email with attachments
        
        Args:
            message: The email message to send
            attachments: List of file paths to attach
            
        Raises:
            SMTPError: If sending fails
            FileNotFoundError: If an attachment doesn't exist
        """
        ...
        
    async def verify_connection(self) -> bool:
        """
        Verify SMTP server connection
        
        Returns:
            True if connection is valid, False otherwise
            
        Raises:
            SMTPError: If connection check fails
        """
        ...

    async def get_server_info(self) -> dict[str, str]:
        """
        Get SMTP server information
        
        Returns:
            Dictionary containing server details (hostname, features)
            
        Raises:
            SMTPError: If fetching server info fails
        """
        ...