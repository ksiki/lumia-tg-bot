from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


class ActionLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        event_from_user = data.get("event_from_user")
        user_id = event_from_user.id if event_from_user else None
        message_text = ""
        
        if isinstance(event, Message):
            message_text = event.text or event.caption or ""

        result = await handler(event, data)

        response_text = ""
        if isinstance(result, Message):
            response_text = result.text or result.caption or ""
        elif isinstance(result, str):
            response_text = result

        if user_id:
            # запись в бд
            pass

        return result