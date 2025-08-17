from typing import Protocol
from sms_gateway.domain.models import Message, GSMModemConfig
from sms_gateway.ports.messaging import MessagingPort

class SMSPort(MessagingPort, Protocol):
    """Protocol for SMS messaging via GSM modem"""
    
    async def initialize(self, config: GSMModemConfig) -> None:
        """
        Initialize the SMS service with GSM modem config
        
        Args:
            config: GSM modem configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
            ModemError: If modem initialization fails
        """
        ...

    async def check_signal_strength(self) -> int:
        """
        Get current signal strength
        
        Returns:
            Signal strength in dBm
            
        Raises:
            ModemError: If reading signal strength fails
        """
        ...
        
    async def get_modem_info(self) -> dict[str, str]:
        """
        Get modem information
        
        Returns:
            Dictionary containing modem details (manufacturer, model, IMEI)
            
        Raises:
            ModemError: If reading modem info fails
        """
        ...