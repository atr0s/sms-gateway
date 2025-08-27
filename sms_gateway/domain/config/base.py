from pydantic import BaseModel, Field, ConfigDict
from .runtime import RuntimeConfig
from .queue import MessageProcessingConfig
from .adapters import AdapterConfig

class SMSGatewayConfig(BaseModel):
    """Top level configuration for the SMS Gateway"""
    model_config = ConfigDict(extra="forbid")  # Prevent unknown fields

    name: str = Field(default="sms-gateway", description="Name of this gateway instance")
    sms: AdapterConfig = Field(description="Configuration for SMS message adapters")
    integration: AdapterConfig = Field(description="Configuration for integration message adapters")
    queues: MessageProcessingConfig = Field(description="Message queue configuration")
    runtime: RuntimeConfig = Field(
        default_factory=RuntimeConfig,
        description="Runtime configuration settings"
    )

class BaseConfig(BaseModel):
    enabled: bool = Field(default=True, description="Whether this service is enabled")
    name: str = Field(description="Service identifier name")