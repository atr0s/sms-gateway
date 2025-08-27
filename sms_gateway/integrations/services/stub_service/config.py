from pydantic import BaseModel, Field

class StubConfig(BaseModel):
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
    enabled: bool = Field(default=True, description="Whether this service is enabled")
    name: str = Field(description="Service identifier name")