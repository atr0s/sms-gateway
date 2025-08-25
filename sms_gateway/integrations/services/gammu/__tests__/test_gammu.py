import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from sms_gateway.domain.messaging import Message, Destination, MessageType
from sms_gateway.integrations.services.gammu.config import GammuConfig
from sms_gateway.integrations.services.gammu.adapter import GammuAdapter

@pytest.fixture
def gammu_config() -> GammuConfig:
    """Fixture providing test Gammu modem configuration"""
    return GammuConfig(
        name="test-gammu",
        enabled=True,
        port="/dev/ttyUSB0",
        connection="at115200"
    )

@pytest.fixture
def gammu_adapter() -> GammuAdapter:
    """Fixture providing a GammuAdapter instance"""
    return GammuAdapter()

@pytest.mark.asyncio(scope="function")
async def test_initialize(gammu_adapter: GammuAdapter, gammu_config: GammuConfig):
    """Test Gammu initialization"""
    with patch('sms_gateway.integrations.services.gammu.adapter.StateMachine') as mock_sm_class:
        # Setup mock
        mock_sm = MagicMock()
        mock_sm_class.return_value = mock_sm
        
        # Initialize adapter
        await gammu_adapter.initialize(gammu_config)
        
        # Verify initialization
        mock_sm_class.assert_called_once()
        mock_sm.SetConfig.assert_called_once_with(0, {
            'Device': gammu_config.port,
            'Connection': gammu_config.connection
        })
        mock_sm.Init.assert_called_once()
        assert gammu_adapter.name == gammu_config.name
        assert gammu_adapter.sm == mock_sm

@pytest.mark.asyncio(scope="function")
async def test_initialize_error(gammu_adapter: GammuAdapter, gammu_config: GammuConfig):
    """Test initialization failure"""
    with patch('sms_gateway.integrations.services.gammu.adapter.StateMachine') as mock_sm_class:
        # Setup mock to raise error
        mock_sm = MagicMock()
        mock_sm.Init.side_effect = Exception("Failed to initialize")
        mock_sm_class.return_value = mock_sm
        
        # Attempt initialization
        with pytest.raises(Exception, match="Failed to initialize"):
            await gammu_adapter.initialize(gammu_config)

@pytest.mark.asyncio(scope="function")
async def test_shutdown(gammu_adapter: GammuAdapter):
    """Test adapter shutdown"""
    with patch('sms_gateway.integrations.services.gammu.adapter.StateMachine') as mock_sm_class:
        # Setup mock
        mock_sm = MagicMock()
        mock_sm_class.return_value = mock_sm
        gammu_adapter.sm = mock_sm
        
        # Shutdown adapter
        await gammu_adapter.shutdown()
        
        # Verify shutdown
        mock_sm.Terminate.assert_called_once()
        assert gammu_adapter.sm is None

@pytest.mark.asyncio(scope="function")
async def test_send_message(gammu_adapter: GammuAdapter):
    """Test sending SMS message through Gammu"""
    # Setup test message
    message = Message(
        content="Test SMS",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender"
    )
    
    # Setup mock modem
    mock_sm = MagicMock()
    gammu_adapter.sm = mock_sm
    
    # Send message
    await gammu_adapter.send_message(message)
    
    # Verify send_sms was called with correct parameters
    mock_sm.SendSMS.assert_called_once_with({
        'Text': message.content,
        'SMSC': {'Location': 1},
        'Number': "+1234567890",
        'Entries': []
    })

@pytest.mark.asyncio(scope="function")
async def test_send_message_not_initialized(gammu_adapter: GammuAdapter):
    """Test sending message when modem is not initialized"""
    message = Message(
        content="Test SMS",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender"
    )
    
    with pytest.raises(RuntimeError, match="Gammu modem not initialized"):
        await gammu_adapter.send_message(message)

@pytest.mark.asyncio(scope="function")
async def test_send_message_error(gammu_adapter: GammuAdapter):
    """Test sending message when Gammu fails"""
    # Setup test message
    message = Message(
        content="Test SMS",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender"
    )
    
    # Setup mock to raise error
    mock_sm = MagicMock()
    mock_sm.SendSMS.side_effect = Exception("Failed to send")
    gammu_adapter.sm = mock_sm
    
    # Attempt to send message
    with pytest.raises(Exception, match="Failed to send"):
        await gammu_adapter.send_message(message)
    
    # Verify send attempt was made
    mock_sm.SendSMS.assert_called_once()

@pytest.mark.asyncio(scope="function")
async def test_get_message(gammu_adapter: GammuAdapter):
    """Test getting a message from Gammu"""
    # Setup mock with available message
    mock_sm = MagicMock()
    mock_sm.GetSMSStatus.return_value = {'SIMUsed': 1, 'PhoneUsed': 0}
    mock_sm.GetNextSMS.return_value = [{
        'Text': 'Test message',
        'Number': '+1234567890',
        'Location': 1
    }]
    gammu_adapter.sm = mock_sm
    
    # Get message
    message = await gammu_adapter.get_message()
    
    # Verify message was retrieved and converted correctly
    assert message is not None
    assert message.content == 'Test message'
    assert message.sender == '+1234567890'
    assert not message.destinations
    
    # Verify status was checked and message was deleted
    mock_sm.GetSMSStatus.assert_called_once()
    mock_sm.GetNextSMS.assert_called_once_with(Start=True, Folder=0)
    mock_sm.DeleteSMS.assert_called_once_with(Folder=0, Location=1)

@pytest.mark.asyncio(scope="function")
async def test_get_message_empty(gammu_adapter: GammuAdapter):
    """Test getting message when none are available"""
    mock_sm = MagicMock()
    mock_sm.GetSMSStatus.return_value = {'SIMUsed': 0, 'PhoneUsed': 0}
    gammu_adapter.sm = mock_sm
    
    message = await gammu_adapter.get_message()
    assert message is None
    mock_sm.GetNextSMS.assert_not_called()

@pytest.mark.asyncio(scope="function")
async def test_get_message_not_initialized(gammu_adapter: GammuAdapter):
    """Test getting message when modem is not initialized"""
    with pytest.raises(RuntimeError, match="Gammu modem not initialized"):
        await gammu_adapter.get_message()

@pytest.mark.asyncio(scope="function")
async def test_get_message_error(gammu_adapter: GammuAdapter):
    """Test getting message when Gammu fails"""
    mock_sm = MagicMock()
    mock_sm.GetSMSStatus.side_effect = Exception("Failed to get status")
    gammu_adapter.sm = mock_sm
    
    with pytest.raises(Exception, match="Failed to get status"):
        await gammu_adapter.get_message()