from typing import Protocol, Iterator
from sms_gateway.domain.models import Message

class MessageQueuePort(Protocol):
    async def enqueue(self, message: Message) -> None:
        """
        Enqueue a message for processing
        
        Args:
            message: The message to enqueue
        
        Raises:
            QueueFullError: If the queue is full
        """
        ...
        
    async def dequeue(self) -> Message:
        """
        Dequeue a message for processing
        
        Returns:
            The next message to process
            
        Raises:
            QueueEmptyError: If the queue is empty
        """
        ...
        
    async def stream(self) -> Iterator[Message]:
        """
        Stream messages as they arrive
        
        Returns:
            Iterator for receiving messages
        """
        ...