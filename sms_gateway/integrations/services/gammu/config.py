from pydantic import BaseModel, Field
from sms_gateway.domain.models import BaseConfig

class GammuConfig(BaseConfig):
    port: str = Field(description="Serial port for the modem device")
    connection: str = Field(default="at115200", description="Connection type and speed (e.g. at115200)")