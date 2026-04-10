import asyncio
from typing import Final
from predictions.predictor import Predictor

from create_bot import BOT, DISPATCHER, DATABASE
from scenarios import START_ROUTER, MENU_ROUTER
from predictions.predictor import Predictor
from database.data_services import DataServices
from database.repositories import UserRepository, TransactionRepository, SubscriptionRepository, ActionLogRepository, CalendarRepository, PredictionRepository, ProductsRepository


async def main() -> None:
    await DATABASE.connect()
    DATA_SERVICES: Final[DataServices] = DataServices(user_rep=UserRepository(DATABASE.pool),
                                                 transaction_rep=TransactionRepository(DATABASE.pool),
                                                 subscription_rep=SubscriptionRepository(DATABASE.pool),
                                                 action_log_rep=ActionLogRepository(DATABASE.pool),
                                                 prediction_rep=PredictionRepository(DATABASE.pool),
                                                 products_rep=ProductsRepository(DATABASE.pool),
                                                 calendar_rep=CalendarRepository(DATABASE.pool))
    PREDICTOR = Predictor(DATA_SERVICES)

    DISPATCHER.include_routers(START_ROUTER, MENU_ROUTER)
    await BOT.delete_webhook(drop_pending_updates=True)
    await DISPATCHER.start_polling(BOT, data_services=DATA_SERVICES, predictor=PREDICTOR)
    await DATABASE.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

