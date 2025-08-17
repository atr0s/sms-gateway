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
    
    async def initialize(self, config: BaseConfig) -> None:
        """Initialize the stub service"""
        self.name = config.name
        print(f"Initialized {self.name} stub incoming service")
    
    async def shutdown(self) -> None:
        """Shutdown the stub service"""
        print(f"Shutting down {self.name} stub incoming service")
    
    async def send_message(self, message: Message) -> None:
        """Not implemented for incoming-only service"""
        print(f"\n{self.name} sending message:")
        print(f"From: {message.sender}")
        print(f"To: {[d.address for d in message.destinations]}")
        print(f"Content: {message.content}\n")


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


