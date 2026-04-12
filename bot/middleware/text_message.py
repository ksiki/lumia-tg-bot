import asyncio
import logging
from logging import Logger
from typing import Callable, Awaitable, Any, Final

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.utils.chat_action import ChatActionSender
from aiogram.dispatcher.flags import get_flag

from common.constants import TEXT_MESSAGE_INTERVAL

LOG: Final[Logger] = logging.getLogger(__name__)
DATA_CHAT: Final[str] = "event_chat"
DATA_BOT: Final[str] = "bot"
SKIP_FLAG: Final[str] = "skip_chat_action"


class TypingActionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        chat = data.get(DATA_CHAT)
        bot = data.get(DATA_BOT)
        
        if not chat or not bot:
            return await handler(event, data)
        
        if get_flag(data, SKIP_FLAG):
            return await handler(event, data)

        try:
            async with ChatActionSender.typing(bot=bot, chat_id=chat.id):
                LOG.info(f"Typing action started for chat: {chat.id}")
                await asyncio.sleep(TEXT_MESSAGE_INTERVAL)
                return await handler(event, data)
        except Exception as e:
            LOG.error(f"Typing action failed for chat {chat.id}: {e}")
            return await handler(event, data)