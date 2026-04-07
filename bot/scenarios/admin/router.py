import logging
from logging import Logger
from typing import Final
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMINS
# from lexicon.vocabulary import Msg


ADMIN_COMMAND_ROUTER: Final[Router] = Router()
LOG: Final[Logger] = logging.getLogger(__name__)


@ADMIN_COMMAND_ROUTER.message(Command("admin"))
async def admin(message: Message) -> None:
    await message.delete()

    user_id: int = message.from_user.id                                                 # pyright: ignore[reportOptionalMemberAccess]
    if user_id not in ADMINS: 
        LOG.info(f"User with id={user_id} try use /admin command")
        return
    
    await message.answer("Just admin")
