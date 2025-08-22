import asyncio
from typing import AsyncIterator
from sms_gateway.domain.models import Message
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.common.logging import get_logger

class QueueFullError(Exception):
    """Raised when attempting to enqueue a message to a full queue"""
    pass

class QueueEmptyError(Exception):
    """Raised when attempting to dequeue from an empty queue"""
    pass

class AsyncInMemoryMessageQueue(MessageQueuePort):
    """Async in-memory implementation of the message queue using asyncio.Queue"""
    
    def __init__(self, maxsize: int = 1000):
        self.logger = get_logger(__name__)
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
            self.logger.debug(f"Enqueueing message: {message}")
            result = self._queue.put_nowait(message)
            self.logger.debug("Message enqueued successfully")
            return result
        except asyncio.QueueFull:
            self.logger.error("Failed to enqueue message: queue is full")
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
            self.logger.debug("Attempting to dequeue message")
            message = self._queue.get_nowait()
            self.logger.debug(f"Dequeued message: {message}")
            return message
        except asyncio.QueueEmpty:
            self.logger.debug("No messages available to dequeue")
            raise QueueEmptyError("Message queue is empty")
    
    async def stream(self) -> AsyncIterator[Message]:
        """
        Asynchronously stream messages as they arrive
        
        Yields:
            Messages as they are added to the queue
        """
        self.logger.debug("Starting message stream")
        while True:
            message = await self._queue.get()
            self.logger.debug(f"Streamed message: {message}")
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