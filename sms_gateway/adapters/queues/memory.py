import asyncio
from typing import AsyncIterator
from sms_gateway.domain.models import Message
from sms_gateway.ports.message_queue import MessageQueuePort

class QueueFullError(Exception):
    """Raised when attempting to enqueue a message to a full queue"""
    pass

class QueueEmptyError(Exception):
    """Raised when attempting to dequeue from an empty queue"""
    pass

class AsyncInMemoryMessageQueue(MessageQueuePort):
    """Async in-memory implementation of the message queue using asyncio.Queue"""
    
    def __init__(self, maxsize: int = 1000):
        """
        Initialize the async in-memory queue
        
        Args:
            maxsize: Maximum number of messages the queue can hold (default: 1000)
        """
        self._queue = asyncio.Queue(maxsize=maxsize)
        
    async def enqueue(self, message: Message) -> None:
        """
        Asynchronously enqueue a message for processing
        
        Args:
            message: The message to enqueue
            
        Raises:
            QueueFullError: If the queue is full
        """
        try:
            return self._queue.put_nowait(message)
        except asyncio.QueueFull:
            raise QueueFullError("Message queue is full")
    
    async def dequeue(self) -> Message:
        """
        Asynchronously dequeue a message for processing
        
        Returns:
            The next message to process
            
        Raises:
            QueueEmptyError: If the queue is empty
        """
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            raise QueueEmptyError("Message queue is empty")
    
    async def stream(self) -> AsyncIterator[Message]:
        """
        Asynchronously stream messages as they arrive
        
        Yields:
            Messages as they are added to the queue
        """
        while True:
            message = await self._queue.get()
            yield message
    
    def size(self) -> int:
        """
        Get the current number of messages in the queue
        
        Returns:
            Current queue size
        """
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty
        
        Returns:
            True if queue is empty, False otherwise
        """
        return self._queue.empty()
    
    def is_full(self) -> bool:
        """
        Check if the queue is full
        
        Returns:
            True if queue is full, False otherwise
        """
        return self._queue.full()