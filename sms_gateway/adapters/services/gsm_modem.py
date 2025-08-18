from typing import Optional
from sms_gateway.domain.models import Message, GSMModemConfig
from sms_gateway.ports.messaging import MessagingPort
from async_gsm_modem.base import ATModem as GsmModem

class GsmModemAdapter(MessagingPort):
    """Adapter for GSM modem using async-gsm-modem library"""
    
    def __init__(self):
        self.name = ""
        self.modem: GsmModem | None = None
        
    async def initialize(self, config: GSMModemConfig) -> None:
        """Initialize the GSM modem with provided configuration
        
        Args:
            config: The modem configuration including port and baud rate
            
        Raises:
            ConfigurationError: If modem initialization fails
        """
        self.name = config.name
        self.modem = GsmModem(
            port=config.port,
            baud_rate=config.baud_rate,
            pin=config.pin
        )
        await self.modem.connect()
        
    async def shutdown(self) -> None:
        """Cleanup and shutdown the modem connection"""
        if self.modem:
            await self.modem.disconnect()
            self.modem = None

    async def send_message(self, message: Message) -> None:
        """Send SMS message through the GSM modem
        
        Args:
            message: The message to send, containing destination numbers and content
            
        Raises:
            MessagingError: If sending fails
            RuntimeError: If modem is not initialized
        """
        if not self.modem:
            raise RuntimeError("GSM modem not initialized")
            
        # Send to all SMS destinations
        for destination in message.destinations:
            await self.modem.send_sms(
                destination.address,
                message.content
            )
        
    async def get_message(self) -> Optional[Message]:
        """Get a single SMS message from the modem
        
        Returns:
            A received message with sender number and content, or None if no messages available
            
        Raises:
            MessagingError: If receiving fails
            RuntimeError: If modem is not initialized
        """
        if not self.modem:
            raise RuntimeError("GSM modem not initialized")
            
        # List available messages
        messages = await self.modem.list_messages()
        if not messages:
            return None
            
        # Get and delete the first message
        sms = messages[0]
        await self.modem.delete_message(sms.index)
        
        # Convert to our Message format
        return Message(
            content=sms.text,
            destinations=[],  # No destinations for received messages
            sender=sms.number
        )