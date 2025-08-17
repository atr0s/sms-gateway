import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sms_gateway.services.base import MessageService
from sms_gateway.domain.models import Message, Destination, MessageType

@pytest.fixture
def mock_port():
    port = Mock()
    port.name = "mock_port"
    port.get_message = AsyncMock()
    port.send_message = AsyncMock()
    return port

@pytest.fixture
def mock_queue():
    queue = Mock()
    queue.enqueue = AsyncMock()
    queue.dequeue = AsyncMock()
    return queue

@pytest.fixture
def test_message():
    return Message(
        content="Test message",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="+0987654321"
    )

@pytest.fixture
def service(mock_port, mock_queue):
    return MessageService(
        name="test_service",
        ports=[mock_port],
        incoming_queue=mock_queue,
        outgoing_queue=mock_queue
    )

@pytest.mark.asyncio
async def test_check_ports_successful_message(service, mock_port, mock_queue, test_message):
    # Setup
    mock_port.get_message.return_value = test_message
    
    # Execute
    await service.check_ports("test_destination")
    
    # Assert
    mock_port.get_message.assert_called_once()
    mock_queue.enqueue.assert_called_once_with(test_message)

@pytest.mark.asyncio
async def test_check_ports_empty_queue(service, mock_port, mock_queue):
    # Setup
    mock_port.get_message.side_effect = asyncio.QueueEmpty()
    
    # Execute
    await service.check_ports("test_destination")
    
    # Assert
    mock_port.get_message.assert_called_once()
    mock_queue.enqueue.assert_not_called()

@pytest.mark.asyncio
async def test_check_ports_error(service, mock_port, mock_queue):
    # Setup
    mock_port.get_message.side_effect = Exception("Test error")
    
    # Execute
    await service.check_ports("test_destination")
    
    # Assert
    mock_port.get_message.assert_called_once()
    mock_queue.enqueue.assert_not_called()

@pytest.mark.asyncio
async def test_process_queue_successful_send(service, mock_port, mock_queue, test_message):
    # Setup
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.return_value = None
    
    # Execute
    await service.process_queue()
    
    # Assert
    mock_queue.dequeue.assert_called_once()
    mock_port.send_message.assert_called_once_with(test_message)
    assert mock_queue.enqueue.call_count == 0  # Message shouldn't be requeued on success

@pytest.mark.asyncio
async def test_process_queue_all_ports_fail(service, mock_port, mock_queue, test_message):
    # Setup
    mock_queue.dequeue.return_value = test_message
    mock_port.send_message.side_effect = Exception("Send failed")
    
    # Execute
    await service.process_queue()
    
    # Assert
    mock_queue.dequeue.assert_called_once()
    mock_port.send_message.assert_called_once_with(test_message)
    assert mock_queue.enqueue.call_count == 0  # Service doesn't requeue on failure
    # Note: The requeue functionality was removed from the base service implementation

@pytest.mark.asyncio
async def test_process_queue_empty(service, mock_queue):
    # Setup
    mock_queue.dequeue.side_effect = Exception("Queue empty")
    
    # Execute
    await service.process_queue()
    
    # Assert
    mock_queue.dequeue.assert_called_once()