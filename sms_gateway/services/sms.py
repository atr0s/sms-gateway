from typing import List
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.services.base import MessageService

class SMSService(MessageService):
    """Service for handling SMS messages"""
    
    def __init__(
        self, 
        ports: List[MessagingPort],
        incoming_queue: MessageQueuePort,
        outgoing_queue: MessageQueuePort
    ):
        """Initialize SMS service
        
        Args:
            ports: List of SMS ports
            incoming_queue: Queue for Integration messages
            outgoing_queue: Queue for SMS messages that need to be sent out
        """
        super().__init__("sms", ports, incoming_queue, outgoing_queue)
        
    async def check_ports(self) -> None:
        """Check SMS ports for new messages and route them to integration"""
        await super().check_ports("integrations")