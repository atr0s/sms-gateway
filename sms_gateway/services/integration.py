from typing import List
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.services.base import MessageService

class IntegrationService(MessageService):
    """Service for handling integration messages"""
    
    def __init__(
        self,
        ports: List[MessagingPort],
        incoming_queue: MessageQueuePort,
        outgoing_queue: MessageQueuePort
    ):
        """Initialize integration service
        
        Args:
            ports: List of integration ports
            incoming_queue: Queue for SMS messages
            outgoing_queue: Queue for Integration messages that need to be sent out
        """
        super().__init__("integration", ports, incoming_queue, outgoing_queue)
        
    async def check_ports(self) -> None:
        """Check integration ports for new messages and route them to SMS"""
        await super().check_ports("SMS")