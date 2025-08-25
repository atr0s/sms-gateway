from pydantic import BaseModel, Field
from typing import List
from sms_gateway.integrations.config import (
    BaseConfig, TelegramConfig, GammuConfig, StubConfig
)

class AdapterConfig(BaseModel):
    """Configuration for message adapters (input/output)"""
    telegram: List[TelegramConfig] | None = Field(default=None, description="List of Telegram adapters")
    email: List[BaseConfig] | None = Field(default=None, description="List of Email adapters")
    gammu: List[GammuConfig] | None = Field(default=None, description="List of Gammu modem adapters")
    stub: List[StubConfig] | None = Field(default=None, description="List of stub adapters")