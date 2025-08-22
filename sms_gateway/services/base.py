from typing import List, Dict, Type
from datetime import datetime
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.domain.models import Message
from sms_gateway.common.logging import get_logger
from sms_gateway.domain.backoff import (
    BackoffStrategy,
    ExponentialBackoff,
    LinearBackoff,
    BackoffConfig
)
import asyncio

class MessageService:
    """Base class for message handling services"""
    
    def __init__(
        self,
        name: str,
        ports: List[MessagingPort],
        incoming_queue: MessageQueuePort,
        outgoing_queue: MessageQueuePort,
        config: BackoffConfig = BackoffConfig()
    ):
        """
        Initialize message service
        
        Args:
            name: Service name for logging
            ports: List of messaging ports
            incoming_queue: Queue for message processing
            outgoing_queue: Queue for message processing
            config: Retry backoff configuration
        """
        self.name = name
        self.ports = ports
        self.incoming_queue = incoming_queue
        self.outgoing_queue = outgoing_queue
        self.backoff_config = config
        self.logger = get_logger(f"service.{name}")
        self.logger.debug(
            f"Initializing message service {name} with "
            f"{len(ports)} ports | "
            f"Incoming queue: {incoming_queue.__class__.__name__} | "
            f"Outgoing queue: {outgoing_queue.__class__.__name__}"
        )
        self._strategy_map: Dict[str, Type[BackoffStrategy]] = {
            "exponential": ExponentialBackoff,
            "linear": LinearBackoff
        }
        self.MAX_RETRIES = 5
        
    async def check_ports(self, route_to: str) -> None:
        """Check ports for new messages and route them to the queue
        
        Args:
            route_to: Destination name for logging
        """
        self.logger.debug(f"Checking {len(self.ports)} ports for new messages to route to {route_to}")
        for port in self.ports:
            try:
                self.logger.debug(f"Checking port {port.name} for messages")
                message = await port.get_message()
                if message is None:
                    self.logger.debug(f"No messages available from port {port.name}")
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
                
    def _get_backoff_strategy(self, strategy_name: str) -> BackoffStrategy:
        """Get the appropriate backoff strategy instance"""
        strategy_cls = self._strategy_map.get(strategy_name, ExponentialBackoff)
        if strategy_cls == ExponentialBackoff:
            return strategy_cls(
                min_delay=self.backoff_config.min_delay,
                max_delay=self.backoff_config.max_delay,
                multiplier=self.backoff_config.multiplier
            )
        return strategy_cls(
            min_delay=self.backoff_config.min_delay,
            max_delay=self.backoff_config.max_delay,
            increment=self.backoff_config.increment
        )

    async def process_queue(self) -> None:
        """Process messages from the queue and attempt delivery through ports"""
        try:
            self.logger.debug("Attempting to dequeue message from incoming queue")
            message = await self.incoming_queue.dequeue()
            now = datetime.utcnow()

            # Check if the message is ready for retry
            if message.retry_count > 0 and message.next_retry_at is not None:
                if now < message.next_retry_at:
                    self.logger.debug(
                        f"Message not ready for retry until {message.next_retry_at} | "
                        f"Current time: {now}"
                    )
                    await self.incoming_queue.enqueue(message)
                    return

            self.logger.info(
                f"Processing {self.name} message from {message.sender} | "
                f"To: {[d.address for d in message.destinations]} | "
                f"Retry: {message.retry_count}/{self.MAX_RETRIES}"
            )
            
            if await self._try_send_message(message):
                # Clear retry info on success
                message.retry_count = 0
                message.last_retry_timestamp = None
                message.next_retry_at = None
                return

            # Update retry info after failed attempt
            message.retry_count += 1
            message.last_retry_timestamp = datetime.utcnow()  # Set after attempt, not before
            
            if message.retry_count >= self.MAX_RETRIES:
                self.logger.error(
                    f"Max retries ({self.MAX_RETRIES}) reached for {self.name} message | "
                    f"From: {message.sender} | "
                    f"To: {[d.address for d in message.destinations]} | "
                    f"Message will be discarded"
                )
                return

            # Calculate next retry time using the actual retry timestamp
            strategy = self._get_backoff_strategy(message.backoff_strategy)
            message.next_retry_at = strategy.calculate_next_retry(
                message.retry_count,
                message.last_retry_timestamp
            )
            
            # Requeue for retry
            self.logger.warning(
                f"All ports failed to send {self.name} message | "
                f"From: {message.sender} | "
                f"To: {[d.address for d in message.destinations]} | "
                f"Retry attempt {message.retry_count}/{self.MAX_RETRIES} | "
                f"Next retry at: {message.next_retry_at}"
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
        self.logger.debug(f"Attempting to send message through {len(self.ports)} available ports")
        for port in self.ports:
            try:
                self.logger.debug(f"Attempting to send message via port {port.name}")
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