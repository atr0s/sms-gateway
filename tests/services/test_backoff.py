import pytest
from datetime import datetime, timedelta
from sms_gateway.domain.models import Message, Destination, MessageType
from sms_gateway.domain.backoff import (
    BackoffConfig,
    ExponentialBackoff,
    LinearBackoff
)
from sms_gateway.services.base import MessageService
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
def test_message():
    return Message(
        content="Test message",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender",
        backoff_strategy="exponential"
    )

@pytest.fixture
def mock_port():
    port = MagicMock()
    port.name = "test-port"
    port.send_message = AsyncMock()
    return port

@pytest.fixture
def mock_queue():
    queue = MagicMock()
    queue.dequeue = AsyncMock()
    queue.enqueue = AsyncMock()
    return queue

@pytest.fixture
def service(mock_port, mock_queue):
    config = BackoffConfig(
        min_delay=1.0,
        max_delay=300.0,
        multiplier=2.0
    )
    return MessageService(
        name="test-service",
        ports=[mock_port],
        incoming_queue=mock_queue,
        outgoing_queue=mock_queue,
        config=config
    )

@pytest.mark.asyncio
async def test_exponential_backoff_timing(service, mock_port, mock_queue, test_message):
    """Test that exponential backoff calculates correct retry times"""
    # Simulate first failure
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.side_effect = Exception("Send failed")
    
    # First retry
    await service.process_queue()
    assert test_message.retry_count == 1
    assert test_message.last_retry_timestamp is not None
    assert test_message.next_retry_at is not None
    
    # Should wait 1 second (min_delay) for first retry
    expected_delay = timedelta(seconds=1)
    actual_delay = test_message.next_retry_at - test_message.last_retry_timestamp
    assert abs(actual_delay - expected_delay) < timedelta(milliseconds=100)

    # Second retry - simulate waiting for retry delay
    first_retry = test_message.last_retry_timestamp
    next_retry_time = test_message.next_retry_at
    with patch('sms_gateway.services.base.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = next_retry_time
        await service.process_queue()
    assert test_message.retry_count == 2
    
    # Should wait 2 seconds (min_delay * multiplier) for second retry
    expected_delay = timedelta(seconds=2)
    actual_delay = test_message.next_retry_at - test_message.last_retry_timestamp
    assert abs(actual_delay - expected_delay) < timedelta(milliseconds=100)

@pytest.mark.asyncio
async def test_linear_backoff_timing(service, mock_port, mock_queue, test_message):
    """Test that linear backoff calculates correct retry times"""
    # Configure for linear backoff
    test_message.backoff_strategy = "linear"
    service.backoff_config.increment = 5.0
    
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.side_effect = Exception("Send failed")
    
    # First retry - should wait min_delay
    await service.process_queue()
    assert test_message.retry_count == 1
    expected_delay = timedelta(seconds=1)
    actual_delay = test_message.next_retry_at - test_message.last_retry_timestamp
    assert abs(actual_delay - expected_delay) < timedelta(milliseconds=100)
    
    # Second retry - simulate waiting for retry delay
    next_retry_time = test_message.next_retry_at
    with patch('sms_gateway.services.base.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = next_retry_time
        await service.process_queue()
    assert test_message.retry_count == 2
    expected_delay = timedelta(seconds=6)  # 1 + 5
    actual_delay = test_message.next_retry_at - test_message.last_retry_timestamp
    assert abs(actual_delay - expected_delay) < timedelta(milliseconds=100)

@pytest.mark.asyncio
async def test_respect_max_delay(service, mock_port, mock_queue, test_message):
    """Test that backoff respects maximum delay setting"""
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.side_effect = Exception("Send failed")
    
    # Run through multiple retries
    for _ in range(10):  # Should hit max delay
        await service.process_queue()
        if test_message.retry_count >= service.MAX_RETRIES:
            break
            
        actual_delay = test_message.next_retry_at - test_message.last_retry_timestamp
        assert actual_delay <= timedelta(seconds=service.backoff_config.max_delay)

@pytest.mark.asyncio
async def test_respect_retry_timing(service, mock_port, mock_queue, test_message):
    """Test that messages aren't retried before their next_retry_at time"""
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.side_effect = Exception("Send failed")
    
    # First attempt
    await service.process_queue()
    
    # Try to process again immediately
    await service.process_queue()
    
    # Should have been re-queued without retry attempt
    assert test_message.retry_count == 1  # Still at first retry
    assert mock_port.send_message.call_count == 1  # Only called once