import pytest
from sms_gateway.domain.models import QueueConfig
from sms_gateway.adapters.queues.factory import create_queue
from sms_gateway.adapters.queues.memory import AsyncInMemoryMessageQueue


def test_create_memory_queue():
    """Test creating a memory queue with default config"""
    config = QueueConfig(type="memory")
    queue = create_queue(config, "test")
    assert isinstance(queue, AsyncInMemoryMessageQueue)


def test_create_memory_queue_with_custom_size():
    """Test creating a memory queue with custom size"""
    config = QueueConfig(type="memory", maxsize=500)
    queue = create_queue(config, "test")
    assert isinstance(queue, AsyncInMemoryMessageQueue)
    # Access internal queue to verify maxsize
    assert queue._queue.maxsize == 500


def test_create_queue_invalid_type():
    """Test error handling for invalid queue type"""
    # Create memory queue but pass invalid type to factory
    config = QueueConfig(type="memory")
    # Override type after creation since QueueConfig validates type
    config.type = "invalid"  # type: ignore
    with pytest.raises(ValueError) as exc:
        create_queue(config, "test")
    assert str(exc.value) == "Unsupported queue type: invalid"