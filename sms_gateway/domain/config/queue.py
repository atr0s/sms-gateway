from pydantic import BaseModel, Field
from typing import Literal

class QueueConfig(BaseModel):
    type: Literal["memory"] = Field(description="Type of queue to use")
    maxsize: int = Field(default=1000, description="Maximum size of the queue")

class MessageProcessingConfig(BaseModel):
    sms_queue: QueueConfig = Field(description="Configuration for SMS message queue")
    integration_queue: QueueConfig = Field(description="Configuration for integration message queue")