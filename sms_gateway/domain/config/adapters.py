from pydantic import BaseModel, Field
from typing import List
from sms_gateway.integrations.services.telegram.config import TelegramConfig
from sms_gateway.integrations.services.gammu.config import GammuConfig
from sms_gateway.integrations.services.stub_service.config import StubConfig


class AdapterConfig(BaseModel):
    """Configuration for message adapters (input/output)"""
    telegram: List[TelegramConfig] | None = Field(default=None, description="List of Telegram adapters")
    gammu: List[GammuConfig] | None = Field(default=None, description="List of Gammu modem adapters")
    stub: List[StubConfig] | None = Field(default=None, description="List of stub adapters")