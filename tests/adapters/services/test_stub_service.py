import pytest
import pytest_asyncio
from sms_gateway.domain.models import Message, Destination, MessageType, StubConfig
from sms_gateway.adapters.services.stub_service import StubSmsService

@pytest_asyncio.fixture
async def stub_service():
    """Initialize and return a StubService for testing"""
    service = StubSmsService()
    # Initialize with test config
    config = StubConfig(name="test-stub", enabled=True)
    await service.initialize(config)
    return service

@pytest.fixture
def normal_message():
    return Message(
        content="Normal test message",
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender",
        retry_count=0
    )

@pytest.fixture
def failure_message():
    return Message(
        content="Test message that will fail",  # Contains 'fail' trigger
        destinations=[
            Destination(type=MessageType.SMS, address="+1234567890")
        ],
        sender="test-sender",
        retry_count=0
    )

@pytest.mark.asyncio
async def test_send_normal_message(stub_service, normal_message):
    """Test that normal messages are delivered successfully"""
    # Verify successful send does not raise exception
    await stub_service.send_message(normal_message)

@pytest.mark.asyncio
async def test_failure_tracking(stub_service, failure_message):
    """Test the failure and retry pattern of the stub service"""
    # First attempt should fail due to trigger word
    with pytest.raises(RuntimeError, match="Message delivery failed on first attempt"):
        await stub_service.send_message(failure_message)
    
    # Second attempt should succeed due to failed_messages tracking
    await stub_service.send_message(failure_message)

@pytest.mark.asyncio
async def test_generated_message_retry_count(stub_service):
    """Test that auto-generated messages have expected retry count"""
    # Configure to always generate messages
    stub_service.message_probability = 1.0
    msg = await stub_service.get_message()
    
    assert msg is not None
    assert msg.retry_count == 0, "Generated messages should start with retry_count=0"

@pytest.mark.asyncio
async def test_get_message_includes_retry_count(stub_service):
    """Test that generated messages include retry count"""
    # Force message generation by setting high probability
    stub_service.message_probability = 1.0
    
    message = await stub_service.get_message()
    assert message is not None
    assert hasattr(message, "retry_count")
    assert message.retry_count == 0  # New messages should start with 0 retries