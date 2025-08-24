from pydantic import BaseModel, Field
from sms_gateway.integrations.config.base import BaseConfig

class StubConfig(BaseConfig):
    message_probability: float = Field(
        default=0.1,
        description="Probability of generating a message (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    delay: float = Field(
        default=1.0,
        description="Delay between message generation attempts in seconds",
        ge=0.1
    )