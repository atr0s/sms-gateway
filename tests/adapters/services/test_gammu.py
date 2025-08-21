import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from sms_gateway.domain.models import GammuConfig
from sms_gateway.adapters.services.gammu import GammuAdapter

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
    with patch('sms_gateway.adapters.services.gammu.StateMachine') as mock_sm_class:
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
    with patch('sms_gateway.adapters.services.gammu.StateMachine') as mock_sm_class:
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
    with patch('sms_gateway.adapters.services.gammu.StateMachine') as mock_sm_class:
        # Setup mock
        mock_sm = MagicMock()
        mock_sm_class.return_value = mock_sm
        gammu_adapter.sm = mock_sm
        
        # Shutdown adapter
        await gammu_adapter.shutdown()
        
        # Verify shutdown
        mock_sm.Terminate.assert_called_once()
        assert gammu_adapter.sm is None