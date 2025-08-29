import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from sms_gateway.daemon import SMSGatewayDaemon, async_main, main
from sms_gateway.domain.config import SMSGatewayConfig, QueueConfig, RuntimeConfig, AdapterConfig, MessageProcessingConfig
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort

@pytest.fixture
def config():
    return SMSGatewayConfig(
        name="test_gateway",
        runtime=RuntimeConfig(poll_delay=0.1),
        queues=MessageProcessingConfig(
            sms_queue=QueueConfig(type="memory", maxsize=100),
            integration_queue=QueueConfig(type="memory", maxsize=100)
        ),
        sms=AdapterConfig(
            stub=[{"name": "stub1"}],
            gammu=None,
            telegram=None
        ),
        integration=AdapterConfig(
            telegram=None,
            stub=None,
            gammu=None
        )
    )

@pytest.fixture
def mock_message_port():
    port = AsyncMock(spec=MessagingPort)
    port.name = "mock_port"
    return port

@pytest.fixture
def mock_queue():
    queue = AsyncMock(spec=MessageQueuePort)
    return queue

@pytest.fixture
def mock_sms_service():
    service = AsyncMock()
    service.check_ports = AsyncMock()
    service.process_queue = AsyncMock()
    return service

@pytest.fixture
def mock_integration_service():
    service = AsyncMock()
    service.check_ports = AsyncMock()
    service.process_queue = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_daemon_initialization(config):
    """Test daemon initialization with config"""
    daemon = SMSGatewayDaemon(config)
    assert daemon.config == config
    assert daemon.should_run == False
    assert isinstance(daemon.sms_ports, list)
    assert isinstance(daemon.integration_ports, list)
    assert daemon.sms_queue is not None
    assert daemon.integration_queue is not None
    assert daemon.sms_service is not None
    assert daemon.integration_service is not None

@pytest.mark.asyncio
async def test_daemon_initialize(config):
    """Test adapter initialization"""
    daemon = SMSGatewayDaemon(config)
    await daemon.initialize()
    
    # Should initialize stub SMS adapter
    assert len(daemon.sms_ports) == 1
    assert daemon.sms_ports[0].name == "stub1"
    
    # No integration adapters configured
    assert len(daemon.integration_ports) == 0

@pytest.mark.asyncio
async def test_daemon_shutdown(config, mock_message_port):
    """Test daemon shutdown process"""
    daemon = SMSGatewayDaemon(config)
    daemon.sms_ports = [mock_message_port]
    daemon.integration_ports = [mock_message_port]
    daemon.should_run = True

    await daemon.shutdown()

    assert daemon.should_run == False
    assert mock_message_port.shutdown.call_count == 2
    
@pytest.mark.asyncio
async def test_check_services(config):
    """Test checking services for new messages"""
    daemon = SMSGatewayDaemon(config)
    daemon.sms_service.check_ports = AsyncMock()
    daemon.integration_service.check_ports = AsyncMock()

    await daemon.check_services()

    assert daemon.sms_service.check_ports.called
    assert daemon.integration_service.check_ports.called

@pytest.mark.asyncio
async def test_process_queues(config):
    """Test processing message queues"""
    daemon = SMSGatewayDaemon(config)
    daemon.sms_service.process_queue = AsyncMock()
    daemon.integration_service.process_queue = AsyncMock()

    await daemon.process_queues()

    assert daemon.sms_service.process_queue.called
    assert daemon.integration_service.process_queue.called

@pytest.mark.asyncio
async def test_run_loop(config):
    """Test main processing loop"""
    daemon = SMSGatewayDaemon(config)
    daemon.initialize = AsyncMock()
    daemon.check_services = AsyncMock()
    daemon.process_queues = AsyncMock()
    daemon.shutdown = AsyncMock()

    # Set should_run to False after 2 cycles
    async def mock_sleep(*args):
        daemon.should_run = False
    
    with patch('asyncio.sleep', mock_sleep):
        await daemon.run()

    assert daemon.initialize.called
    assert daemon.check_services.called
    assert daemon.process_queues.called
    assert daemon.shutdown.called

@pytest.mark.asyncio
async def test_async_main_valid_config():
    """Test async_main with valid config"""
    mock_config = SMSGatewayConfig(
        name="test",
        runtime=RuntimeConfig(poll_delay=0.1),
        queues=MessageProcessingConfig(
            sms_queue=QueueConfig(type="memory", maxsize=100),
            integration_queue=QueueConfig(type="memory", maxsize=100)
        ),
        sms=AdapterConfig(stub=None, gammu=None, telegram=None),
        integration=AdapterConfig(telegram=None, stub=None, gammu=None)
    )

    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('sms_gateway.daemon.load_config') as mock_load, \
         patch('sms_gateway.daemon.SMSGatewayDaemon.run') as mock_run:

        mock_args.return_value.config = Path('config.json')
        mock_load.return_value = mock_config
        mock_run.return_value = None

        result = await async_main()
        assert result == 0
        assert mock_load.called
        assert mock_run.called

@pytest.mark.asyncio 
async def test_async_main_invalid_config():
    """Test async_main with invalid config"""
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('sms_gateway.daemon.load_config') as mock_load:

        mock_args.return_value.config = Path('config.json')
        mock_load.side_effect = Exception("Invalid config")

        result = await async_main()
        assert result == 1
