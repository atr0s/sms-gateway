import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from sms_gateway.domain.models import (
    GSMModemConfig,
    Message,
    Destination,
    MessageType
)
from sms_gateway.adapters.services.gsm_modem import GsmModemAdapter

@pytest.fixture
def gsm_config() -> GSMModemConfig:
    """Fixture providing test GSM modem configuration"""
    return GSMModemConfig(
        name="test-modem",
        enabled=True,
        port="/dev/ttyUSB0",
        baud_rate=115200,
        pin="1234"
    )

@pytest.fixture
def gsm_adapter() -> GsmModemAdapter:
    """Fixture providing a GsmModemAdapter instance"""
    return GsmModemAdapter()

@pytest.fixture(autouse=True)
async def cleanup_adapter(gsm_adapter: GsmModemAdapter):
    """Cleanup fixture to ensure adapter is properly shutdown"""
    yield
    if gsm_adapter.modem:
        await gsm_adapter.shutdown()

@pytest.mark.asyncio(scope="function")
async def test_initialize(gsm_adapter: GsmModemAdapter, gsm_config: GSMModemConfig):
    """Test modem initialization"""
    with patch('sms_gateway.adapters.services.gsm_modem.GsmModem') as mock_modem_class:
        # Setup mock
        mock_modem = AsyncMock()
        mock_modem_class.return_value = mock_modem
        
        # Initialize adapter
        await gsm_adapter.initialize(gsm_config)
        
        # Verify initialization
        mock_modem_class.assert_called_once_with(
            port=gsm_config.port,
            baud_rate=gsm_config.baud_rate,
            pin=gsm_config.pin
        )
        mock_modem.connect.assert_awaited_once()
        assert gsm_adapter.name == gsm_config.name
        assert gsm_adapter.modem == mock_modem

@pytest.mark.asyncio(scope="function")
async def test_shutdown(gsm_adapter: GsmModemAdapter):
    """Test adapter shutdown"""
    # Setup mock
    mock_modem = AsyncMock()
    gsm_adapter.modem = mock_modem
    
    # Shutdown adapter
    await gsm_adapter.shutdown()
    
    # Verify shutdown
    mock_modem.disconnect.assert_awaited_once()
    assert gsm_adapter.modem is None

@pytest.mark.asyncio(scope="function")
async def test_send_message(gsm_adapter: GsmModemAdapter, gsm_config: GSMModemConfig):
    """Test sending SMS message through modem"""
    # Setup test message
    message = Message(
        content="Test SMS",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender"
    )
    
    # Setup mock modem
    mock_modem = AsyncMock()
    gsm_adapter.modem = mock_modem
    
    # Send message
    await gsm_adapter.send_message(message)
    
    # Verify send_sms was called with correct parameters
    mock_modem.send_sms.assert_awaited_once_with(
        "+1234567890",
        "Test SMS"
    )

@pytest.mark.asyncio(scope="function")
async def test_send_message_not_initialized(gsm_adapter: GsmModemAdapter):
    """Test sending message when modem is not initialized"""
    message = Message(
        content="Test SMS",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender"
    )
    
    with pytest.raises(RuntimeError, match="GSM modem not initialized"):
        await gsm_adapter.send_message(message)

@pytest.mark.asyncio(scope="function")
async def test_get_message(gsm_adapter: GsmModemAdapter):
    """Test getting a message from the modem"""
    # Setup mock modem and message
    mock_modem = AsyncMock()
    mock_sms = MagicMock()
    mock_sms.text = "Test message"
    mock_sms.number = "+1234567890"
    mock_sms.index = 1
    mock_modem.list_messages.return_value = [mock_sms]
    gsm_adapter.modem = mock_modem
    
    # Get message
    message = await gsm_adapter.get_message()
    
    # Verify modem interactions
    mock_modem.list_messages.assert_awaited_once()
    mock_modem.delete_message.assert_awaited_once_with(mock_sms.index)
    
    # Verify message contents
    assert message is not None
    assert message.content == "Test message"
    assert message.sender == "+1234567890"
    assert not message.destinations  # Should be empty for received messages

@pytest.mark.asyncio(scope="function")
async def test_get_message_empty(gsm_adapter: GsmModemAdapter):
    """Test getting message when none are available"""
    # Setup mock modem with no messages
    mock_modem = AsyncMock()
    mock_modem.list_messages.return_value = []
    gsm_adapter.modem = mock_modem
    
    assert await gsm_adapter.get_message() is None
    mock_modem.list_messages.assert_awaited_once()

@pytest.mark.asyncio(scope="function")
async def test_get_message_not_initialized(gsm_adapter: GsmModemAdapter):
    """Test getting message when modem is not initialized"""
    with pytest.raises(RuntimeError, match="GSM modem not initialized"):
        await gsm_adapter.get_message()
