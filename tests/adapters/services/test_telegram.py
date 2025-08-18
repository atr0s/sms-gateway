import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update
from telegram.ext import Application, ContextTypes

from sms_gateway.domain.models import (
    Message, MessageType, Destination,
    TelegramConfig
)
from sms_gateway.adapters.services.telegram import TelegramAdapter

@pytest.fixture
def telegram_config() -> TelegramConfig:
    """Fixture providing test Telegram configuration"""
    return TelegramConfig(
        name="test-bot",
        enabled=True,
        bot_token="test-token",
        chat_id="test-chat"
    )

@pytest.fixture
def test_message() -> Message:
    """Fixture providing a test message"""
    return Message(
        content="Test message",
        destinations=[
            Destination(type=MessageType.TELEGRAM, address="test-chat")
        ],
        sender="test-sender"
    )

@pytest.fixture
def telegram_adapter() -> TelegramAdapter:
    """Fixture providing a TelegramAdapter instance"""
    return TelegramAdapter()

@pytest.fixture(autouse=True)
async def cleanup_adapter(telegram_adapter: TelegramAdapter):
    """Cleanup fixture to ensure adapter is properly shutdown"""
    yield
    if telegram_adapter.app:
        await telegram_adapter.shutdown()


@pytest.mark.asyncio(scope="function")
async def test_shutdown(telegram_adapter: TelegramAdapter):
    """Test adapter shutdown"""
    # Setup mocks
    mock_app = AsyncMock()
    mock_updater = AsyncMock()
    mock_app.updater = mock_updater
    telegram_adapter.app = mock_app
    
    # Shutdown adapter
    await telegram_adapter.shutdown()
    
    # Verify shutdown
    mock_app.updater.stop.assert_awaited_once()
    mock_app.stop.assert_awaited_once()
    mock_app.shutdown.assert_awaited_once()

@pytest.mark.asyncio(scope="function")
async def test_send_message(telegram_adapter: TelegramAdapter, telegram_config: TelegramConfig, test_message: Message):
    """Test sending messages through Telegram"""
    # Setup mocks
    mock_app = AsyncMock()
    mock_bot = AsyncMock()
    mock_app.bot = mock_bot
    telegram_adapter.app = mock_app
    telegram_adapter.config = telegram_config
    
    # Send message
    await telegram_adapter.send_message(test_message)
    
    # Verify message sending
    expected_text = f"From: {test_message.sender}\nMessage: {test_message.content}"
    mock_app.bot.send_message.assert_awaited_once_with(
        chat_id=telegram_config.chat_id,
        text=expected_text
    )

@pytest.mark.asyncio(scope="function")
async def test_send_message_not_initialized(telegram_adapter: TelegramAdapter, test_message: Message):
    """Test sending message when adapter is not initialized"""
    with pytest.raises(RuntimeError, match="Telegram bot not initialized"):
        await telegram_adapter.send_message(test_message)

@pytest.mark.asyncio(scope="function")
async def test_handle_valid_sms_command(telegram_adapter: TelegramAdapter):
    """Test handling valid SMS command"""
    # Setup mocks
    update = MagicMock(spec=Update)
    update.message = AsyncMock()
    update.message.text = '/sms +1234567890 "Test SMS message"'
    update.message.chat_id = 123456
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Handle command
    await telegram_adapter._handle_sms_command(update, context)
    
    # Get and verify the queued message
    message = await telegram_adapter.get_message()
    assert message.content == "Test SMS message"
    assert message.destinations[0].type == MessageType.SMS
    assert message.destinations[0].address == "+1234567890"
    assert message.sender == "123456"
    
    # Verify reply was sent
    update.message.reply_text.assert_awaited_once_with('Message queued for sending')

@pytest.mark.asyncio(scope="function")
async def test_handle_invalid_sms_command_format(telegram_adapter: TelegramAdapter):
    """Test handling invalid SMS command format"""
    # Setup mocks
    update = MagicMock(spec=Update)
    update.message = AsyncMock()
    update.message.text = '/sms invalid format'
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Handle command
    await telegram_adapter._handle_sms_command(update, context)
    
    # Verify error response
    update.message.reply_text.assert_awaited_once_with(
        'Invalid format. Use: /sms +CCNNNNNNNNN "message"'
    )

@pytest.mark.asyncio(scope="function")
async def test_handle_invalid_phone_number(telegram_adapter: TelegramAdapter):
    """Test handling invalid phone number in SMS command"""
    # Setup mocks
    update = MagicMock(spec=Update)
    update.message = AsyncMock()
    update.message.text = '/sms 123456 "Test message"'  # Missing + prefix
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Handle command
    await telegram_adapter._handle_sms_command(update, context)
    
    # Verify error response
    update.message.reply_text.assert_awaited_once_with(
        'Invalid format. Use: /sms +CCNNNNNNNNN "message"'
    )

@pytest.mark.asyncio(scope="function")
async def test_get_message_when_empty(telegram_adapter: TelegramAdapter):
    """Test getting message from empty queue returns None"""
    message = await telegram_adapter.get_message()
    assert message is None