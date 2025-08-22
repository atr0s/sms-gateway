from typing import List
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.domain.models import Message
from sms_gateway.common.logging import get_logger
import asyncio

class MessageService:
    """Base class for message handling services"""
    
    def __init__(
        self,
        name: str,
        ports: List[MessagingPort],
        incoming_queue: MessageQueuePort,
        outgoing_queue: MessageQueuePort
    ):
        """
        Initialize message service
        
        Args:
            name: Service name for logging
            ports: List of messaging ports
            incoming_queue: Queue for message processing
            outgoing_queue: Queue for message processing
        """
        self.name = name
        self.ports = ports
        self.incoming_queue = incoming_queue
        self.outgoing_queue = outgoing_queue
        self.logger = get_logger(f"service.{name}")
        
    async def check_ports(self, route_to: str) -> None:
        """Check ports for new messages and route them to the queue
        
        Args:
            route_to: Destination name for logging
        """
        for port in self.ports:
            try:
                message = await port.get_message()
                if message is None:
                    continue
                    
                self.logger.debug(f"Received {self.name} message: {message}")
                
                await self.outgoing_queue.enqueue(message)
                self.logger.info(
                    f"Routed message from {message.sender} | "
                    f"Service: {self.name} | "
                    f"To: {route_to}"
                )
            except Exception as e:
                error_msg = f"Error processing {self.name} message via {port.name}: {e}"
                self.logger.error(error_msg)
                
    async def process_queue(self) -> None:
        """Process messages from the queue and attempt delivery through ports"""
        MAX_RETRIES = 5

        try:
            message = await self.incoming_queue.dequeue()
            
            self.logger.info(
                f"Processing {self.name} message from {message.sender} | "
                f"To: {[d.address for d in message.destinations]} | "
                f"Retry: {message.retry_count}/{MAX_RETRIES}"
            )
            
            if await self._try_send_message(message):
                return
                
            # No ports succeeded, check retry count
            message.retry_count += 1
            
            if message.retry_count >= MAX_RETRIES:
                self.logger.error(
                    f"Max retries ({MAX_RETRIES}) reached for {self.name} message | "
                    f"From: {message.sender} | "
                    f"To: {[d.address for d in message.destinations]} | "
                    f"Message will be discarded"
                )
                return
                
            # Requeue for retry
            self.logger.warning(
                f"All ports failed to send {self.name} message | "
                f"From: {message.sender} | "
                f"To: {[d.address for d in message.destinations]} | "
                f"Retry attempt {message.retry_count}/{MAX_RETRIES}"
            )
            await self.incoming_queue.enqueue(message)
            
        except Exception as e:
            # Queue might be empty, that's normal
            if "empty" not in str(e).lower():
                self.logger.error(f"Error processing {self.name} queue: {e}")
                
    async def _try_send_message(
        self,
        message: Message
    ) -> bool:
        """Try to send a message through available ports until successful
        
        Args:
            message: Message to send
            
        Returns:
            True if message was sent successfully, False if all ports failed
        """
        for port in self.ports:
            try:
                await port.send_message(message)
                self.logger.info(
                    f"Successfully sent {self.name} message via {port.name} | "
                    f"From: {message.sender} | "
                    f"To: {[d.address for d in message.destinations]} | "
                    f"Content: {message.content[:30]}..."
                )
                return True
            except Exception as e:
                self.logger.error(
                    f"Failed to send through {port.name} | "
                    f"From: {message.sender} | "
                    f"Error: {str(e)}"
                )
                continue
        return False