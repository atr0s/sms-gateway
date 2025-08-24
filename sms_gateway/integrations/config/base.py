from pydantic import BaseModel, Field

class BaseConfig(BaseModel):
    enabled: bool = Field(default=True, description="Whether this service is enabled")
    name: str = Field(description="Service identifier name")