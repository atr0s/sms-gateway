from typing import Optional
from gammu import StateMachine
from sms_gateway.domain.models import Message, GammuConfig
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.adapters.services.registry import AdapterRegistry, AdapterType
from sms_gateway.common.logging import get_logger

@AdapterRegistry.register(AdapterType.SMS, "gammu")
class GammuAdapter(MessagingPort):
    """Adapter for SMS messaging using python-gammu library"""
    
    def __init__(self):
        self.name = ""
        self.sm: StateMachine | None = None
        self.logger = get_logger("gammu")
        
    async def initialize(self, config: GammuConfig) -> None:
        """Initialize the Gammu state machine with provided configuration
        
        Args:
            config: The modem configuration including port and baud rate
            
        Raises:
            ConfigurationError: If Gammu initialization fails
        """
        self.name = config.name
        
        try:
            # Create and configure state machine
            self.sm = StateMachine()
            device_cfg = {
                'Device': config.port,
                'Connection': config.connection
            }
            
            # Initialize the state machine with configuration
            self.sm.SetConfig(0, device_cfg)
            self.sm.Init()
            
            self.logger.info(
                f"Initialized Gammu modem {self.name} on port {config.port} "
                f"with connection {config.connection}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gammu modem {self.name}: {e}")
            raise
    async def shutdown(self) -> None:
        """Cleanup and shutdown Gammu connection"""
        if self.sm:
            try:
                # Terminate the Gammu connection
                self.sm.Terminate()
                self.sm = None
                self.logger.info(f"Gammu modem {self.name} disconnected")
            except Exception as e:
                self.logger.error(f"Error disconnecting Gammu modem {self.name}: {e}")
                raise
    async def send_message(self, message: Message) -> None:
        """Send SMS message through Gammu
        
        Args:
            message: The message to send, containing destination numbers and content
            
        Raises:
            MessagingError: If sending fails
            RuntimeError: If Gammu is not initialized
        """
        if not self.sm:
            raise RuntimeError("Gammu modem not initialized")
            
        # Send to all SMS destinations
        for destination in message.destinations:
            try:
                sms = {
                    'Text': message.content,
                    'SMSC': {'Location': 1},
                    'Number': destination.address
                }
                
                # Send the message
                self.sm.SendSMS(sms)
                
                self.logger.info(
                    f"Sent SMS via {self.name} | To: {destination.address} | "
                    f"Content: {message.content[:30]}..."
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to send SMS via {self.name} | "
                    f"To: {destination.address} | Error: {e}"
                )
                raise
    async def get_message(self) -> Optional[Message]:
        """Get a single SMS message from Gammu
        
        Returns:
            A received message with sender number and content, or None if no messages available
            
        Raises:
            MessagingError: If receiving fails
            RuntimeError: If Gammu is not initialized
        """
        if not self.sm:
            raise RuntimeError("Gammu modem not initialized")
            
        try:
            # Get the first available message
            status = self.sm.GetSMSStatus()
            print(status)
            if status['SIMUsed'] + status['PhoneUsed'] == 0:
                return None
                
            messages = self.sm.GetNextSMS(Start=True)
            if not messages:
                return None
                
            # Get the first message
            sms = messages[0]
            
            # Delete the message after reading
            self.sm.DeleteSMS(Folder=0, Location=sms['Location'])
            
            self.logger.info(
                f"Received SMS via {self.name} | From: {sms['Number']} | "
                f"Content: {sms['Text'][:30]}..."
            )
            
            # Convert to our Message format
            return Message(
                content=sms['Text'],
                destinations=[],  # No destinations for received messages
                sender=sms['Number']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get SMS via {self.name}: {e}")
            raise