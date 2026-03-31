import asyncio
from create_bot import BOT, DISPATCHER

from scenarios.start.router import START_ROUTER
from scenarios.admin.router import ADMIN_COMMAND_ROUTER


async def main() -> None:
    DISPATCHER.include_routers(START_ROUTER, ADMIN_COMMAND_ROUTER)
    await BOT.delete_webhook(drop_pending_updates=True)
    await DISPATCHER.start_polling(BOT)


if __name__ == "__main__":
    asyncio.run(main())
