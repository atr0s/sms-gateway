from pydantic import BaseModel, Field
from .types import MessageType

class Destination(BaseModel):
    type: MessageType
    address: str = Field(description="Phone number, email address, or chat ID depending on type")