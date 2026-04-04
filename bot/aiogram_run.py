import asyncio
from typing import Final
from create_bot import BOT, DISPATCHER, DATABASE

from scenarios.start.router import START_ROUTER
from scenarios.admin.router import ADMIN_COMMAND_ROUTER
from database.data_services import DataServices
from database.repositories.user_repository import UserRepository
from database.repositories.transaction_repository import TransactionRepository
from database.repositories.subscription_repository import SubscriptionRepository
from database.repositories.action_log_repository import ActionLogRepository
from database.repositories.prediction_repository import PredictionRepository
from database.repositories.products_repository import ProductsRepository


async def main() -> None:
    await DATABASE.connect()
    data_services: Final[DataServices] = DataServices(user_rep=UserRepository(DATABASE.pool),
                                                 transaction_rep=TransactionRepository(DATABASE.pool),
                                                 subscription_rep=SubscriptionRepository(DATABASE.pool),
                                                 action_log_rep=ActionLogRepository(DATABASE.pool),
                                                 prediction_rep=PredictionRepository(DATABASE.pool),
                                                 products_rep=ProductsRepository(DATABASE.pool))

    DISPATCHER.include_routers(START_ROUTER, ADMIN_COMMAND_ROUTER)
    await BOT.delete_webhook(drop_pending_updates=True)
    await DISPATCHER.start_polling(BOT, data_services=data_services)
    await DATABASE.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

