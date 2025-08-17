import pytest
import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, List
from sms_gateway.domain.models import Message, MessageType, Destination
from sms_gateway.adapters.queues.memory import (
    AsyncInMemoryMessageQueue,
    QueueFullError,
    QueueEmptyError
)

@pytest.fixture
def test_message() -> Message:
    """Fixture providing a test message"""
    return Message(
        content="Test message",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890"),
            Destination(type=MessageType.TELEGRAM, address="@test_user")
        ],
        sender="test-sender",
        priority=0
    )

@pytest.fixture
def empty_queue() -> AsyncInMemoryMessageQueue:
    """Fixture providing an empty queue with default size"""
    return AsyncInMemoryMessageQueue()

@pytest.fixture
def small_queue() -> AsyncInMemoryMessageQueue:
    """Fixture providing a queue with size 1"""
    return AsyncInMemoryMessageQueue(maxsize=1)

@pytest.mark.asyncio
async def test_queue_init():
    """Test queue initialization with different sizes"""
    queue = AsyncInMemoryMessageQueue()
    assert queue.size() == 0
    assert queue.is_empty()
    assert not queue.is_full()

    queue = AsyncInMemoryMessageQueue(maxsize=1)
    assert queue.size() == 0
    assert queue.is_empty()
    assert not queue.is_full()

@pytest.mark.asyncio
async def test_enqueue_dequeue_basic(empty_queue: AsyncInMemoryMessageQueue, test_message: Message):
    """Test basic enqueue and dequeue operations"""
    # Queue should start empty
    assert empty_queue.is_empty()
    
    # Enqueue a message
    await empty_queue.enqueue(test_message)
    assert not empty_queue.is_empty()
    assert empty_queue.size() == 1
    
    # Dequeue the message
    msg = await empty_queue.dequeue()
    assert msg == test_message
    assert empty_queue.is_empty()

@pytest.mark.asyncio
async def test_queue_full_error(small_queue: AsyncInMemoryMessageQueue, test_message: Message):
    """Test queue full behavior"""
    # Fill the queue
    await small_queue.enqueue(test_message)
    assert small_queue.is_full()
    
    # Try to enqueue to a full queue
    with pytest.raises(QueueFullError):
        await small_queue.enqueue(test_message)

@pytest.mark.asyncio
async def test_queue_empty_error(empty_queue: AsyncInMemoryMessageQueue):
    """Test queue empty behavior"""
    with pytest.raises(QueueEmptyError):
        await empty_queue.dequeue()

@pytest.mark.asyncio
async def test_queue_size(empty_queue: AsyncInMemoryMessageQueue, test_message: Message):
    """Test queue size tracking"""
    assert empty_queue.size() == 0
    
    # Add some messages
    await empty_queue.enqueue(test_message)
    assert empty_queue.size() == 1
    
    await empty_queue.enqueue(test_message)
    assert empty_queue.size() == 2
    
    # Remove a message
    await empty_queue.dequeue()
    assert empty_queue.size() == 1

@pytest.mark.asyncio
async def test_queue_stream(empty_queue: AsyncInMemoryMessageQueue, test_message: Message):
    """Test queue streaming iterator"""
    # Create a stream
    stream = empty_queue.stream()
    assert isinstance(stream, AsyncIterator)

    # Start stream consumer task
    received_messages = []
    consumer = asyncio.create_task(async_consume_stream(stream, received_messages))

    try:
        # Add a message and wait briefly for it to be consumed
        await empty_queue.enqueue(test_message)
        await asyncio.sleep(0.1)
        
        # Verify message was received
        assert len(received_messages) == 1
        assert received_messages[0] == test_message
    finally:
        consumer.cancel()

async def async_consume_stream(stream: AsyncIterator[Message], messages: List[Message]):
    """Helper to consume messages from stream"""
    async for message in stream:
        messages.append(message)

@pytest.mark.asyncio
async def test_fifo_order(empty_queue: AsyncInMemoryMessageQueue):
    """Test First-In-First-Out message ordering"""
    messages = [
        Message(
            content=f"Message {i}",
            destinations=[
                Destination(type=MessageType.SMS, address="+1234567890"),
                Destination(type=MessageType.TELEGRAM, address="@test_user")
            ],
            sender="test-sender",
            priority=0
        )
        for i in range(3)
    ]
    
    # Enqueue messages in order
    for msg in messages:
        await empty_queue.enqueue(msg)
    
    # Dequeue messages and verify order
    for i, expected in enumerate(messages):
        msg = await empty_queue.dequeue()
        assert msg.content == f"Message {i}"
        assert msg == expected

@pytest.mark.asyncio
async def test_queue_stress(empty_queue: AsyncInMemoryMessageQueue, test_message: Message):
    """Test queue under heavy load"""
    # Enqueue many messages
    for _ in range(100):
        await empty_queue.enqueue(test_message)
    assert empty_queue.size() == 100
    
    # Dequeue half
    for _ in range(50):
        await empty_queue.dequeue()
    assert empty_queue.size() == 50
    
    # Enqueue more
    for _ in range(25):
        await empty_queue.enqueue(test_message)
    assert empty_queue.size() == 75
    
    # Dequeue all
    while not empty_queue.is_empty():
        await empty_queue.dequeue()
    assert empty_queue.size() == 0