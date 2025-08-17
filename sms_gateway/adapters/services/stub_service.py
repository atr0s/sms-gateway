import random
import asyncio
from typing import Iterator
from sms_gateway.domain.models import (
    Message, BaseConfig, Destination, MessageType,
)
from sms_gateway.ports.messaging import MessagingPort

class StubSmsService(MessagingPort):
    """Stub implementation that randomly generates incoming messages"""
    
    def __init__(self):
        self.counter = 0
        self.failed_messages = set()  # Track failed message hashes
    
    async def initialize(self, config: BaseConfig) -> None:
        """Initialize the stub service"""
        self.name = config.name
        print(f"Initialized {self.name} stub incoming service")
    
    async def shutdown(self) -> None:
        """Shutdown the stub service"""
        print(f"Shutting down {self.name} stub incoming service")
    
    async def send_message(self, message: Message) -> None:
        """Simulate sending a message with failure simulation capabilities.
        
        Messages containing trigger words ('fail', 'error', 'crash', 'exception')
        will fail on their first attempt but succeed on subsequent retries.
        This simulates transient failures common in messaging systems.
        
        Args:
            message: The message to send
            
        Raises:
            RuntimeError: On first attempt when message contains trigger words
        """
        print(f"\n{self.name} sending message:")
        print(f"From: {message.sender}")
        print(f"To: {[d.address for d in message.destinations]}")
        print(f"Content: {message.content}\n")

        # Generate a unique message identifier based on content and destinations
        msg_hash = hash((message.content, tuple(d.address for d in message.destinations)))

        # Check if message contains trigger words and hasn't failed before
        failure_triggers = ['fail', 'error', 'crash', 'exception']
        if any(trigger in message.content.lower() for trigger in failure_triggers):
            if msg_hash not in self.failed_messages:
                # First attempt - fail and record the failure
                self.failed_messages.add(msg_hash)
                raise RuntimeError("Message delivery failed on first attempt - retry should succeed")


    async def get_message(self) -> Message:
        """
        Randomly generate incoming message with 1/10 probability
        
        Returns:
            A randomly generated message
            
        Raises:
            QueueEmpty: If no message is generated
        """
        # 1 in 10 chance of receiving a message
        if random.random() < 0.1:
            self.counter += 1
            return Message(
                content=f"Test message {self.counter} from {self.name}",
                destinations=[
                    Destination(
                        type=MessageType.TELEGRAM,
                        address="1234567890"
                    )
                ],
                sender=f"+1555{random.randint(1000000,9999999)}"
            )
        raise asyncio.QueueEmpty


