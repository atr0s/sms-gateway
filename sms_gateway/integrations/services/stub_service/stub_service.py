import random
from typing import Optional
from sms_gateway.domain.models import Message, Destination, MessageType
from sms_gateway.integrations.config import StubConfig
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.integrations.services.registry import AdapterRegistry, AdapterType
from sms_gateway.common.logging import get_logger

@AdapterRegistry.register(AdapterType.SMS, "stub")
class StubSmsService(MessagingPort):
    """Stub implementation that randomly generates incoming messages"""
    
    def __init__(self):
        self.counter = 0
        self.failed_messages = set()  # Track failed message hashes
        self.name = ""
        self.message_probability = 0.1
        self.logger = get_logger("stub_service")
    
    async def initialize(self, config: StubConfig) -> None:
        """Initialize the stub service
        
        Args:
            config: Configuration for the stub service
        """
        self.name = config.name
        self.message_probability = config.message_probability
        self.logger.info(f"Initialized {self.name} stub service with probability {self.message_probability}")
    
    async def shutdown(self) -> None:
        """Shutdown the stub service"""
        self.logger.info(f"Shutting down {self.name} stub service")
    
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
        self.logger.info(
            f"Sending message via {self.name} | From: {message.sender} | "
            f"To: {[d.address for d in message.destinations]} | "
            f"Content: {message.content[:50]}..."
        )

        # Generate a unique message identifier based on content and destinations
        msg_hash = hash((message.content, tuple(d.address for d in message.destinations)))

        # Check if message contains trigger words and hasn't failed before
        failure_triggers = ['fail', 'error', 'crash', 'exception']
        if any(trigger in message.content.lower() for trigger in failure_triggers):
            # Track message state by its hash
            failed_before = msg_hash in self.failed_messages
            
            if not failed_before:
                # First attempt - record the failure
                self.failed_messages.add(msg_hash)
                self.logger.warning(f"Simulating transient failure for message from {message.sender}")
                raise RuntimeError("Message delivery failed on first attempt - retry should succeed")
            else:
                # This message failed before, but now succeeds
                self.logger.info(f"Retry succeeded for message from {message.sender}")

    async def get_message(self) -> Optional[Message]:
        """
        Randomly generate incoming message based on configured probability
        
        Returns:
            A randomly generated message, or None if no message is generated
        """
        if random.random() < self.message_probability:
            self.counter += 1
            message = Message(
                content=f"Test message {self.counter} from {self.name}",
                destinations=[
                    Destination(
                        type=MessageType.TELEGRAM,
                        address="1234567890"
                    )
                ],
                sender=f"+1555{random.randint(1000000,9999999)}",
                retry_count=0  # Start with no retries for new messages
            )
            self.logger.info(
                f"Generated test message via {self.name} | "
                f"From: {message.sender} | "
                f"Content: {message.content[:50]}..."
            )
            return message
        return None