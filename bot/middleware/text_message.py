import asyncio
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.utils.chat_action import ChatActionSender
from typing import Callable, Awaitable, Any

from common.constants import TEXT_MESSAGE_INTERVAL


class TypingActionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        chat = data.get("event_chat")
        if not chat:
            return await handler(event, data)

        async with ChatActionSender.typing(bot=data["bot"], chat_id=chat.id):
            await asyncio.sleep(TEXT_MESSAGE_INTERVAL)
            return await handler(event, data)
