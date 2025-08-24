from pydantic import BaseModel, Field
from sms_gateway.integrations.config.base import BaseConfig

class TelegramConfig(BaseConfig):
    bot_token: str = Field(description="Telegram bot API token")
    api_base_url: str = Field(default="https://api.telegram.org", description="Telegram API base URL")
    chat_id: str = Field(description="The Telegram Chat ID")
    name: str = Field(description='Descriptive name for the integration')