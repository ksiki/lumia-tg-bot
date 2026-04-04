import logging
import asyncio
from logging import Logger
from typing import Final
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TOKEN, PG_LINK, REDIS_LINK, DEBUG
from database.core.database import Database
from database.data_services import DataServices
from database.repositories.user_repository import UserRepository
from database.repositories.transaction_repository import TransactionRepository
from database.repositories.subscription_repository import SubscriptionRepository
from database.repositories.action_log_repository import ActionLogRepository
from database.repositories.prediction_repository import PredictionRepository
from database.repositories.products_repository import ProductsRepository

log_level = logging.DEBUG if DEBUG else logging.ERROR
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG: Final[Logger] = logging.getLogger(__name__)

DATABASE: Final[Database] = Database(PG_LINK)
asyncio.run(DATABASE.connect())
DATA_SERVICE: Final[DataServices] = DataServices(user_rep=UserRepository(DATABASE.pool),
                                                 transaction_rep=TransactionRepository(DATABASE.pool),
                                                 subscription_rep=SubscriptionRepository(DATABASE.pool),
                                                 action_log_rep=ActionLogRepository(DATABASE.pool),
                                                 prediction_rep=PredictionRepository(DATABASE.pool),
                                                 products_rep=ProductsRepository(DATABASE.pool))

storage = RedisStorage.from_url(REDIS_LINK)
DISPATCHER: Final[Dispatcher] = Dispatcher(storage=storage)

BOT: Final[Bot] = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
