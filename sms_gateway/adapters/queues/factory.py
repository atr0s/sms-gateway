from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.domain.config import QueueConfig
from sms_gateway.adapters.queues.memory import AsyncInMemoryMessageQueue


def create_queue(queue_config: QueueConfig, queue_type: str) -> MessageQueuePort:
    """
    Create a message queue from configuration

    Args:
        queue_config: Queue configuration
        queue_type: Type of queue for logging
            
    Returns:
        Initialized message queue
            
    Raises:
        ValueError: If queue type is not supported
    """
    if queue_config.type == "memory":
        return AsyncInMemoryMessageQueue(
            maxsize=queue_config.maxsize
        )
    raise ValueError(f"Unsupported queue type: {queue_config.type}")