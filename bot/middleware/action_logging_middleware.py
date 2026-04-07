import logging
from logging import Logger
from typing import Any, Awaitable, Callable, Final
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from database.DTO import ActionLogDTO


LOG: Final[Logger] = logging.getLogger(__name__)


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

        data_services = data.get("data_services")
        if user_id and data_services:
            try:
                event_date = event.date
                log = ActionLogDTO(user_id, 
                                message_text,
                                response_text,
                                event_date.date(),
                                event_date.time())
                
                await data_services.add_new_action_log(log)
            except Exception as e:
                LOG.error(f"Error in {__name__}: {e}")

        return result