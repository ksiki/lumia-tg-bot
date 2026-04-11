import logging
from logging import Logger
from typing import Final
from aiogram import F, Bot, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.DTO import TransactionDTO
from predictions.predictor import Predictor
from lexicon.vocabulary import Buttons, Msg
from database.data_services import DataServices
from middleware.action_logging_middleware import ActionLoggingMiddleware
from middleware.text_message import TypingActionMiddleware
from scenarios.fsm_states import States
from scenarios.message_sendler import send_message
from scenarios.stars_refunder import refund_payment
from scenarios.menu.keyboard import (ProductCallback, get_menu_kb, 
                                     CANCEL, CANCEL_CALLBACK_DATA,
                                     OPEN_MENU, OPEN_MENU_CALLBACK_DATA)
from common.constants import CURRENCY


MENU_ROUTER: Final[Router] = Router()
MENU_ROUTER.message.middleware(ActionLoggingMiddleware())
MENU_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


@MENU_ROUTER.message(F.text == Buttons.ACTIVATE.text, States.MENU)
@MENU_ROUTER.callback_query(F.data == OPEN_MENU_CALLBACK_DATA, States.MENU)
async def menu_handler(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices):
    return await send_main_menu(event, state, data_services)


async def send_main_menu(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices):
    message = event if isinstance(event, Message) else event.message
    
    await state.set_state(States.CHOICE)
    return await send_message(
        message,
        Msg.MENU_MESSAGE.text,
        state,
        States.CHOICE,
        await get_menu_kb(data_services, message.chat.id)
    )


@MENU_ROUTER.callback_query(ProductCallback.filter(), States.CHOICE)
async def handle_product_click(callback: CallbackQuery, state: FSMContext, callback_data: ProductCallback, data_services: DataServices) -> Message:
    await callback.answer("")
    await callback.message.delete()
    
    try:
        product = await data_services.get_product(callback_data.product_id)
    except:
        pass

    item_name = product["name"]
    item_description = product["description"]
    payload = callback_data.product_id + ":" + str(callback_data.is_subscriber)
    
    prices = [LabeledPrice(label=item_name, amount=1)]

    await state.set_state(States.CONFIRM_PAYMENT)
    return await callback.message.answer_invoice(
        title=item_name,
        description=item_description,
        prices=prices,
        payload=payload,
        currency=CURRENCY,
        provider_token="",
        reply_markup=CANCEL
    )


@MENU_ROUTER.pre_checkout_query(States.CONFIRM_PAYMENT)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    LOG.info("Confirm payment")
    await pre_checkout_query.answer(ok=True)


@MENU_ROUTER.callback_query(F.data == CANCEL_CALLBACK_DATA, States.CONFIRM_PAYMENT)
async def payment_cancel(callback: CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    LOG.info("Payment Cancel")
    await callback.answer("")
    await callback.message.delete()
    await state.set_state(States.CHOICE)
    return await send_main_menu(callback, state, data_services)


@MENU_ROUTER.message(F.successful_payment, States.CONFIRM_PAYMENT)
async def process_successful_payment(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    await message.delete()
    payment_info = message.successful_payment

    LOG.info(f"Payment: {payment_info.total_amount} start. UserId: {message.chat.id}. Payload: {payment_info.invoice_payload}")

    try:
        tran_dto = TransactionDTO(
            message.chat.id,
            payment_info.invoice_payload.split(":")[0],
            datetime.now().date(),
            datetime.now().time(),
            payment_info.total_amount,
            message.successful_payment.telegram_payment_charge_id,
            bool(int(payment_info.invoice_payload.split(":")[1]))
        )
        transaction_id = await data_services.add_new_transaction(tran_dto)
    except:
        await refund_payment(message.bot, message.chat.id, message.successful_payment.telegram_payment_charge_id)
        await failed_send_prediction()

    await failed_send_prediction_refund(message, state, data_services, transaction_id)

async def failed_send_prediction():
    pass

async def failed_send_prediction_refund(message: Message, state: FSMContext, data_services: DataServices, transaction_id: int) -> None:
    LOG.info(f"Failed send prediction. refund_payment:{refund_payment}, transaction_id:{transaction_id}")

    transaction = await data_services.get_transaction(transaction_id)

    await send_message(
        message,
        Msg.FAILED_PREDICTION_REFUND.text,
        state,
        States.MENU,
        OPEN_MENU
    )
    await refund_payment(message.bot, message.chat.id, transaction["token"],  data_services, transaction_id)
