from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .destination import Destination

class Message(BaseModel):
    content: str = Field(description="Message content/body")
    destinations: List[Destination] = Field(description="List of destinations to send the message to")
    sender: str = Field(description="Sender identifier (phone number, email, etc)")
    priority: int = Field(default=0, description="Message priority (0 = normal, 1 = high)")
    retry_count: int = Field(default=0, description="Number of retry attempts for failed message delivery")
    last_retry_timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the last retry attempt")
    next_retry_at: Optional[datetime] = Field(default=None, description="When to attempt the next retry")
    backoff_strategy: str = Field(default="exponential", description="Backoff strategy to use (exponential or linear)")