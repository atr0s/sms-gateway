from pydantic import BaseModel, Field

class TelegramConfig(BaseModel):
    bot_token: str = Field(description="Telegram bot API token")
    api_base_url: str = Field(default="https://api.telegram.org", description="Telegram API base URL")
    chat_id: str = Field(description="The Telegram Chat ID")
    enabled: bool = Field(default=True, description="Whether this service is enabled")
    name: str = Field(description="Service identifier name")