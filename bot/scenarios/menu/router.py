from asyncio import Queue
from functools import partial
import logging
from logging import Logger
from typing import Final
from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.DTO import TransactionDTO, PredictionDTO
from predictions.predictor import Predictor
from lexicon.vocabulary import Buttons, Msg
from database.data_services import DataServices
from middleware.action_logging_middleware import ActionLoggingMiddleware
from middleware.text_message import TypingActionMiddleware
from scenarios.fsm_states import States
from scenarios.message_sendler import send_message
from scenarios.stars_refunder import refund_payment_by_charge_id
from utils.validator import is_valid_data_for_prediction
from scenarios.menu.keyboard import (ProductCallback, get_menu_kb, 
                                     PAY, PAY_CALLBACK_DATA,
                                     OPEN_MENU, OPEN_MENU_CALLBACK_DATA,
                                     CANCEL, CANCEL_CALLBACK_DATA)
from common.constants import CURRENCY


MENU_ROUTER: Final[Router] = Router()
MENU_ROUTER.message.middleware(ActionLoggingMiddleware())
MENU_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


#===============================================================================================================================================
# main menu
@MENU_ROUTER.message(F.text == Buttons.ACTIVATE.text, States.MENU)
@MENU_ROUTER.callback_query(F.data == OPEN_MENU_CALLBACK_DATA, States.MENU)
async def menu_handler(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    return await send_main_menu(event, state, data_services)


async def send_main_menu(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> None:
    message = event if isinstance(event, Message) else event.message
    return await send_message(
        message,
        Msg.MENU_MESSAGE.text,
        state,
        States.REQUEST_DATA,
        await get_menu_kb(data_services, message.chat.id)
    )


#===============================================================================================================================================
# request data from user
@MENU_ROUTER.callback_query(ProductCallback.filter(), States.REQUEST_DATA)
async def request_data(
    callback: CallbackQuery, 
    state: FSMContext, 
    callback_data: ProductCallback,
    predictor: Predictor, 
    scheduler: AsyncIOScheduler,
    pdf_queue: Queue, 
    data_services: DataServices
) -> Message:
    await callback.message.delete()
    
    if callback_data.category == "microtransaction":
        await state.clear()
        await state.update_data(
            product_id=callback_data.product_id,
            fact_price=callback_data.fact_price,
            is_subscriber=callback_data.is_subscriber 
        )

        msg = get_message(callback_data.product_id)
        return await send_message(
            callback.message,
            msg,
            state,
            States.SAVE_REQUEST_DATA,
            CANCEL
        )

    tran_dto = TransactionDTO(
        callback.message.chat.id,
        callback_data.product_id,
        datetime.now().date(),
        datetime.now().time(),
        callback_data.fact_price,
        None,
        callback_data.is_subscriber
    )
    await handle_user_request(
        callback.message,
        state,
        predictor,
        scheduler,
        pdf_queue,
        data_services,
        tran_dto
    )    


@MENU_ROUTER.message(F.text, States.SAVE_REQUEST_DATA)
async def save_request_data(message: Message, state: FSMContext) -> Message:
    await message.delete()
    text = message.text
    if not is_valid_data_for_prediction(text):
        return await send_message(
            message,
            Msg.FAILED_DATA_FOR_PREDICTION.text
        )
    
    await state.update_data(
        data_for_prediction=text
    )
    await handle_product_click()


def get_message(prod_str_id: str) -> str:
    match prod_str_id:
        case "one_time_deep_seven_card_hand":
            return Msg.REQUEST_DATA_FOR_DEEP_UNDERSTANDING.text
        case "fate_matrix":
            return Msg.REQUEST_DATA_MATRIX_OF_DESTINY.text
        case "human_design":
            return Msg.REQUEST_DATA_HUMAN_DESIGN.text
        case "deep_compatibility_analysis_synastry":
            return Msg.REQUEST_DATA_COMPATIBILITY_CHART.text
        case "test_of_loyalty":
            return Msg.REQUEST_DATA_TEST_OF_LOYALTY.text


#===============================================================================================================================================
# handle payments
async def handle_product_click(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    await message.delete()
    
    try:
        temp_data = await state.get_data()
        product_id = temp_data["product_id"]
        fact_price = temp_data["fact_price"]
        is_subscriber = temp_data["is_subscriber"]

        product = await data_services.get_product(product_id)
        item_name = product["name"]
        item_description = product["description"]
        payload = product_id + ":" + str(is_subscriber)
        prices = [LabeledPrice(label=item_name, amount=1)]

        await state.set_state(States.CONFIRM_PAYMENT)
        return await message.answer_invoice(
            title=item_name,
            description=item_description,
            prices=prices,
            payload=payload,
            currency=CURRENCY,
            provider_token="",
            reply_markup=PAY
        )
    except:
        LOG.error("Failed send answer invoice")
        await send_message(
            message,
            Msg.FAILED_ANSWER_INVOICE.text,
            state,
            States.MENU,
            OPEN_MENU
        )


@MENU_ROUTER.pre_checkout_query(States.CONFIRM_PAYMENT)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    LOG.info("Confirm payment")
    await pre_checkout_query.answer(ok=True)


@MENU_ROUTER.message(F.successful_payment, States.CONFIRM_PAYMENT)
async def process_successful_payment(
    message: Message, 
    state: FSMContext, 
    predictor: Predictor, 
    scheduler: AsyncIOScheduler,
    pdf_queue: Queue, 
    data_services: DataServices
) -> Message:
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
            payment_info.telegram_payment_charge_id,
            bool(int(payment_info.invoice_payload.split(":")[1]))
        )

        temp_data = await state.get_data()
        await state.clear()
        await handle_user_request(
            message,
            state,
            predictor,
            scheduler,
            pdf_queue,
            data_services,
            tran_dto,
            temp_data["data_for_prediction"]
        )
    except:
        await failed_send_prediction(
            message,
            state,
            refund_method=partial(
                refund_payment_by_charge_id, 
                message.bot, 
                message.chat.id, 
                payment_info.telegram_payment_charge_id, 
                data_services
            )
        )
    
    try:
        await refund_payment_by_charge_id(message.bot, message.chat.id, message.successful_payment.telegram_payment_charge_id, data_services)
    except:
        pass


#===============================================================================================================================================
# send prediction
async def handle_user_request(
    message: Message, 
    state: FSMContext, 
    predictor: Predictor, 
    scheduler: AsyncIOScheduler,
    pdf_queue: Queue, 
    data_services: DataServices, 
    tran_dto: TransactionDTO,
    **kwargs
) -> None:
    await state.set_state(States.WAITING_PREDICTION)
    if tran_dto.product_str_id == "monthly_subscription":
        await data_services.handle_purchase(tran_dto)
        await send_message(
            message,
            Msg.SECCESSFUL_SUBSCRIPTION_PURCHASE.text,
            state,
            States.MENU,
            OPEN_MENU
        )
        return
    
    await send_messgae_waiting_prediction(message)

    product = await data_services.get_product(tran_dto.product_str_id)
    category = product["category"]
    gen_result = await predictor.generate_prediction(tran_dto.user_id, tran_dto.product_str_id, **kwargs)
    if not gen_result["success"]:
        raise RuntimeError()
    
    pred_dto = PredictionDTO(
        tran_dto.user_id, 
        tran_dto.date_transaction,
        None,
        gen_result["type"],
        gen_result["category"],
        gen_result["prediction"],
        gen_result["success"],
        gen_result["cards"],
        gen_result["with_pdf"]
    )
    tran_id, pred_id = await data_services.handle_purchase(tran_dto, pred_dto)
    
    if category == "microtransaction":
        pdf_queue.put((
            pred_id,
            f"{tran_dto.user_id}_{tran_id}_{pred_id}",
            scheduler,
            send_prediction,
            [message, state, pred_id],
            failed_send_prediction,
            [message, state, tran_id]
        ))
    elif category in ("free_service", "subscription_service"):
        await send_service(message, state, pred_id)
    else:
        LOG.error(f"Unknown str_id: {tran_dto.product_str_id} - {category}")
        raise TypeError()


async def send_messgae_waiting_prediction(message: Message) -> Message:
    return await send_message(
        message,
        Msg.WAITING_FOR_PREDICTION.text    
    )


async def send_prediction(message: Message, state: FSMContext, prediction_id: int, path_to_pdf: str):
    LOG.warning("send_prediction")


async def send_service(message: Message, state: FSMContext, prediction_id: int):
    LOG.warning("send_service")


#===============================================================================================================================================
# fail handlers
async def failed_send_prediction(message: Message, state: FSMContext, refund_method):
    LOG.info(f"Prediction failed")
    if refund_method:
        await refund_method()
    await send_message(
        message,
        Msg.FAILED_PREDICTION_REFUND.text,
        state,
        States.MENU,
        OPEN_MENU
    )


@MENU_ROUTER.callback_query(F.data == PAY_CALLBACK_DATA, States.CONFIRM_PAYMENT)
@MENU_ROUTER.message(F.data == CANCEL_CALLBACK_DATA, States.SAVE_REQUEST_DATA)
async def payment_cancel(event: CallbackQuery | Message, state: FSMContext, data_services: DataServices) -> Message:
    LOG.info("Prediction canceled")
    message = event if isinstance(event, Message) else event.message
    await message.answer("")
    await message.message.delete()
    await state.set_state(States.SEND_INVOICE)
    return await send_main_menu(message, state, data_services)