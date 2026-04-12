import logging
from logging import Logger
from typing import Any, Awaitable, Callable, Final
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from database.DTO import ActionLogDTO

LOG: Final[Logger] = logging.getLogger(__name__)
USER_KEY: Final[str] = "event_from_user"
SERVICES_KEY: Final[str] = "data_services"


class ActionLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        user = data.get(USER_KEY)
        user_id = user.id if user else None

        message_text = self.__extract_text(event)
        result = await handler(event, data)
        response_text = result if isinstance(result, str) else self.__extract_text(result)

        data_services = data.get(SERVICES_KEY)
        if user_id and data_services:
            await self.__save_log(data_services, user_id, message_text, response_text, event)

        return result

    def __extract_text(self, obj: Any) -> str:
        if isinstance(obj, Message):
            return obj.text or obj.caption or ""
        return ""

    async def __save_log(self, services: Any, user_id: int, msg_text: str, resp_text: str, event: Any) -> None:
        try:
            dt = event.date
            log_entry = ActionLogDTO(
                user_id,
                msg_text,
                resp_text,
                dt.date(),
                dt.time()
            )
            
            await services.add_new_action_log(log_entry)
            LOG.info(f"Action log saved for user {user_id}")
        except Exception as e:
            LOG.error(f"Failed to save action log: {e}")