import re
import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters
)

from sms_gateway.domain.models import (
    Message, MessageType, Destination,
    TelegramConfig
)
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.common.logging import get_logger
from sms_gateway.adapters.services.registry import AdapterRegistry, AdapterType

PHONE_PATTERN = re.compile(r'^\+\d{1,3}\d{4,14}$')
SMS_COMMAND_PATTERN = re.compile(r'^/sms\s+(\+\d+)\s+"([^"]+)"$')

@AdapterRegistry.register(AdapterType.INTEGRATION, "telegram")
class TelegramAdapter(MessagingPort):
    """Telegram bot adapter implementation"""
    
    def __init__(self):
        self.config: Optional[TelegramConfig] = None
        self.app: Optional[Application] = None
        self.logger = get_logger("telegram")
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self.name = ""
        
    async def initialize(self, config: TelegramConfig) -> None:
        """Initialize Telegram bot with configuration
        
        Args:
            config: Telegram bot configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self.name = config.name
        self.app = Application.builder().token(config.bot_token).build()
        
        # Add command handlers
        self.app.add_handler(CommandHandler("sms", self._handle_sms_command))
        
        # Set unique updater name based on config name
        self.app.updater._id = config.name
        
        # Start the bot
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        self.logger.info(f"Initialized Telegram bot {self.name} with chat ID {config.chat_id}")
        
    async def shutdown(self) -> None:
        """Shutdown the Telegram bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self.logger.info(f"Telegram bot {self.name} shutdown complete")
            
    async def send_message(self, message: Message) -> None:
        """Send a message through Telegram
        
        Args:
            message: Message to send
            
        Raises:
            RuntimeError: If bot is not initialized
        """
        if not self.app:
            raise RuntimeError("Telegram bot not initialized")

        # Format message
        full_text_message = f"From: {message.sender}\nMessage: {message.content}"            
        
        try:
            await self.app.bot.send_message(
                chat_id=self.config.chat_id,
                text=full_text_message
            )
            self.logger.info(
                f"Sent message via {self.name} | To: chat {self.config.chat_id} | "
                f"From: {message.sender} | Content: {message.content[:30]}..."
            )
        except Exception as e:
            self.logger.error(
                f"Failed to send message via {self.name} | "
                f"To: chat {self.config.chat_id} | Error: {e}"
            )
            raise
                
    async def get_message(self) -> Optional[Message]:
        """Get a single message from the queue
        
        Returns:
            The next message in the queue, or None if no messages are available
        """
        try:
            message = self._message_queue.get_nowait()
            if message:
                self.logger.info(
                    f"Got message from queue via {self.name} | "
                    f"To: {[d.address for d in message.destinations]} | "
                    f"Content: {message.content[:30]}..."
                )
            return message
        except asyncio.QueueEmpty:
            return None
    
    async def _handle_sms_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /sms command from Telegram"""
        if not update.message or not update.message.text:
            return
            
        # Parse command
        match = SMS_COMMAND_PATTERN.match(update.message.text)
        if not match:
            await update.message.reply_text(
                'Invalid format. Use: /sms +CCNNNNNNNNN "message"'
            )
            return
            
        phone_number, message_text = match.groups()
        
        # Validate phone number
        if not PHONE_PATTERN.match(phone_number):
            await update.message.reply_text(
                'Invalid phone number format. Use international format: +CCNNNNNNNNN'
            )
            return
            
        # Create message
        message = Message(
            content=message_text,
            destinations=[
                Destination(
                    type=MessageType.SMS,
                    address=phone_number
                )
            ],
            sender=str(update.message.chat_id)
        )
        
        # Add to queue
        await self._message_queue.put(message)
        self.logger.info(
            f"Queued SMS message via {self.name} | "
            f"From: {message.sender} | To: {phone_number} | "
            f"Content: {message_text[:30]}..."
        )
        await update.message.reply_text('Message queued for sending')
