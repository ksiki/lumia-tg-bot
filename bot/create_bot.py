import logging
from logging import Logger
from typing import Final
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TOKEN, PG_LINK, REDIS_LINK, DEBUG
from database.core.database import Database

log_level = logging.DEBUG if DEBUG else logging.ERROR
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG: Final[Logger] = logging.getLogger(__name__)

DATABASE: Final[Database] = Database(PG_LINK)

storage = RedisStorage.from_url(REDIS_LINK)
DISPATCHER: Final[Dispatcher] = Dispatcher(storage=storage)

BOT: Final[Bot] = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
