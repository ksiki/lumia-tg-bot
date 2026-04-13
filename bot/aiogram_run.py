import asyncio
from typing import Final
from predictions.predictor import Predictor

from create_bot import BOT, DISPATCHER, DATABASE, SCHEDULER
from scenarios import START_ROUTER, MENU_ROUTER, USER_SETTINGS_ROUTER, ADMIN_ROUTER
from utils.pdf_generator import pdf_worker, PDF_QUEUE
from predictions.predictor import Predictor
from database.data_services import DataServices


async def main() -> None:
    await DATABASE.connect()
    DATA_SERVICES: Final[DataServices] = DataServices(DATABASE.pool)
    
    PREDICTOR = Predictor(DATA_SERVICES)
    SCHEDULER.start()
    asyncio.create_task(pdf_worker(DATA_SERVICES))

    DISPATCHER.include_routers(ADMIN_ROUTER, MENU_ROUTER, USER_SETTINGS_ROUTER, START_ROUTER)
    await BOT.delete_webhook(drop_pending_updates=True)
    await DISPATCHER.start_polling(
        BOT, 
        data_services=DATA_SERVICES, 
        predictor=PREDICTOR, 
        scheduler=SCHEDULER, 
        pdf_queue=PDF_QUEUE
    )
    await DATABASE.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

