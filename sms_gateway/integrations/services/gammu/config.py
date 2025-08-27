from pydantic import BaseModel, Field

class GammuConfig(BaseModel):
    port: str = Field(description="Serial port for the modem device")
    connection: str = Field(default="at115200", description="Connection type and speed (e.g. at115200)")
    enabled: bool = Field(default=True, description="Whether this service is enabled")
    name: str = Field(description="Service identifier name")