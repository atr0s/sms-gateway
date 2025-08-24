from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime
from .backoff import BackoffConfig
from sms_gateway.integrations.config import (
    BaseConfig, TelegramConfig, GammuConfig, StubConfig
)

class MessageType(Enum):
    SMS = "sms"
    TELEGRAM = "telegram"
    EMAIL = "email"

class Destination(BaseModel):
    type: MessageType
    address: str = Field(description="Phone number, email address, or chat ID depending on type")

class Message(BaseModel):
    content: str = Field(description="Message content/body")
    destinations: List[Destination] = Field(description="List of destinations to send the message to")
    sender: str = Field(description="Sender identifier (phone number, email, etc)")
    priority: int = Field(default=0, description="Message priority (0 = normal, 1 = high)")
    retry_count: int = Field(default=0, description="Number of retry attempts for failed message delivery")
    last_retry_timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the last retry attempt")
    next_retry_at: Optional[datetime] = Field(default=None, description="When to attempt the next retry")
    backoff_strategy: str = Field(default="exponential", description="Backoff strategy to use (exponential or linear)")

class EmailConfig(BaseConfig):
    smtp_host: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port")
    username: str = Field(description="SMTP auth username")
    password: str = Field(description="SMTP auth password")
    use_tls: bool = Field(default=True, description="Whether to use TLS")
    from_address: str = Field(description="Default sender email address")

class QueueConfig(BaseModel):
    type: Literal["memory"] = Field(description="Type of queue to use")
    maxsize: int = Field(default=1000, description="Maximum size of the queue")

class MessageProcessingConfig(BaseModel):
    sms_queue: QueueConfig = Field(description="Configuration for SMS message queue")
    integration_queue: QueueConfig = Field(description="Configuration for integration message queue")

class AdapterConfig(BaseModel):
    """Configuration for message adapters (input/output)"""
    telegram: List[TelegramConfig] | None = Field(default=None, description="List of Telegram adapters")
    email: List[EmailConfig] | None = Field(default=None, description="List of Email adapters")
    gammu: List[GammuConfig] | None = Field(default=None, description="List of Gammu modem adapters")
    stub: List[StubConfig] | None = Field(default=None, description="List of stub adapters")

class RuntimeConfig(BaseModel):
    """Runtime configuration for the gateway"""
    poll_delay: float = Field(
        default=1.0,
        description="Delay in seconds between message polling cycles",
        ge=0.1,  # Minimum 100ms delay
        le=60.0  # Maximum 60s delay
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    backoff: BackoffConfig = Field(
        default_factory=BackoffConfig,
        description="Retry backoff configuration"
    )

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