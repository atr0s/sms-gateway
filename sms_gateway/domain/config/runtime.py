from pydantic import BaseModel, Field
from ..backoff import BackoffConfig

class LoggingComponentConfig(BaseModel):
    """Component-specific logging configuration"""
    default: str = Field(
        default="INFO",
        description="Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Component-specific log levels"
    )
    
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
        description="Legacy logging level (for backwards compatibility)"
    )
    logging: LoggingComponentConfig = Field(
        default_factory=LoggingComponentConfig,
        description="Logging configuration"
    )
    backoff: BackoffConfig = Field(
        default_factory=BackoffConfig,
        description="Retry backoff configuration"
    )