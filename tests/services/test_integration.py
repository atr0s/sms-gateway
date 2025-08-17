import pytest
from unittest.mock import Mock, AsyncMock
from sms_gateway.services.integration import IntegrationService
from sms_gateway.domain.models import Message, Destination, MessageType

@pytest.fixture
def mock_port():
    port = Mock()
    port.name = "mock_integration_port"
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
        content="Test integration message",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="integration-sender-id"
    )

@pytest.fixture
def integration_service(mock_port, mock_queue):
    return IntegrationService(
        ports=[mock_port],
        incoming_queue=mock_queue,
        outgoing_queue=mock_queue
    )

@pytest.mark.asyncio
async def test_check_ports_routes_to_sms(integration_service, mock_port, mock_queue, test_message):
    # Setup
    mock_port.get_message.return_value = test_message
    
    # Execute
    await integration_service.check_ports()
    
    # Assert
    mock_port.get_message.assert_called_once()
    mock_queue.enqueue.assert_called_once_with(test_message)

@pytest.mark.asyncio
async def test_integration_service_name(integration_service):
    assert integration_service.name == "integration"