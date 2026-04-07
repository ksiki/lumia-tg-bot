import logging
from logging import Logger
from typing import Final
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from lexicon.vocabulary import Buttons, Msg
from database.data_services import DataServices
from middleware.action_logging_middleware import ActionLoggingMiddleware
from middleware.text_message import TypingActionMiddleware
from scenarios.fsm_states import States
from scenarios.message_sendler import send_message
from scenarios.menu.keyboard import ProductCallback, get_menu_kb


MENU_ROUTER: Final[Router] = Router()
MENU_ROUTER.message.middleware(ActionLoggingMiddleware())
MENU_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


@MENU_ROUTER.message(F.text.in_(Buttons.ACTIVATE.text), States.MENU)
async def menu(message: Message, state: FSMContext, data_services: DataServices) -> Message | None:
    LOG.info("Main menu")
    return await send_message(message,
                              Msg.MENU_MESSAGE.text,
                              state,
                              States.CHOICE,
                              await get_menu_kb(data_services, message.from_user.id))


@MENU_ROUTER.callback_query(ProductCallback.filter(), States.CHOICE)
async def handle_product_click(callback: CallbackQuery, callback_data: ProductCallback):
    await callback.answer("")
    product_id = callback_data.product_id
    await callback.message.answer(f"Вы выбрали продукт с ID: {product_id}")