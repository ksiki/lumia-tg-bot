import json
import logging
import random
from asyncio import Queue
from functools import partial
from logging import Logger
from typing import Final, Any
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import or_f, and_f
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.DTO import TransactionDTO, PredictionDTO, GetPredictionDTO
from predictions.predictor import Predictor
from lexicon.vocabulary import Buttons, Msg
from database.data_services import DataServices
from middleware import ActionLoggingMiddleware, TypingActionMiddleware
from scenarios.fsm_states import States
from scenarios.message_sendler import create_delayed_message, send_message, send_prediction, send_service
from scenarios.stars_refunder import refund_payment_by_charge_id
from utils.validator import is_valid_data_for_prediction
from scenarios.menu.keyboard import (
    ProductCallback, get_menu_kb, 
    ServiceMessageData, get_service_mess_kb,
    PAY, CANCEL, OPEN_MENU,
    CANCEL_PAY_CALLBACK_DATA, OPEN_MENU_CALLBACK_DATA, CANCEL_CALLBACK_DATA,
    SETTINGS_CALLBACK_DATA
)
from common.constants import CURRENCY, FIRE_MESSAGE_EFFECT_ID, DEBUG_WAIT
from config import ADMINS, DEBUG, DIRRECT_LINK, STARS_SHOP_LINK

MENU_ROUTER: Final[Router] = Router()
MENU_ROUTER.message.middleware(ActionLoggingMiddleware())
MENU_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)

CAT_SUBSCRIPTION: Final[str] = "subscription"
CAT_MICROTRANSACTION: Final[str] = "microtransaction"
CAT_FREE_SERVICE: Final[str] = "free_service"
CAT_SUB_SERVICE: Final[str] = "subscription_service"
PROD_MONTHLY_SUB: Final[str] = "monthly_subscription"
PRICE_FOR_ADMINS: Final[int] = 1

REQUEST_MESSAGES: Final[dict[str, str]] = {
    "one_time_deep_seven_card_hand": Msg.REQUEST_DATA_FOR_DEEP_UNDERSTANDING.text,
    "fate_matrix": Msg.REQUEST_DATA_MATRIX_OF_DESTINY.text,
    "human_design": Msg.REQUEST_DATA_HUMAN_DESIGN.text,
    "deep_compatibility_analysis_synastry": Msg.REQUEST_DATA_COMPATIBILITY_CHART.text,
    "test_of_loyalty": Msg.REQUEST_DATA_TEST_OF_LOYALTY.text
}


#===============================================================================================================================================
# main menu
@MENU_ROUTER.callback_query(
    or_f(
        and_f(F.data == OPEN_MENU_CALLBACK_DATA, States.MENU),
        and_f(F.data == CANCEL_CALLBACK_DATA, States.REQUEST_DATA)
    )
)
@MENU_ROUTER.message(F.text == Buttons.ACTIVATE.text, States.MENU)
async def menu_handler(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    return await send_main_menu(event, state, data_services)


async def send_main_menu(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    if isinstance(event, CallbackQuery):
        await event.answer("")

    message = event if isinstance(event, Message) else event.message
    promotion_text = await data_services.get_text_promotion()
    msg_text = Msg.MENU_MESSAGE.format(
        promotion=promotion_text,
        dirrect_link=DIRRECT_LINK,
        stars_shop_link=STARS_SHOP_LINK
    )
    return await send_message(
        message,
        msg_text,
        state,
        States.CHOICE,
        await get_menu_kb(data_services, message.chat.id)
    )


async def update_main_mune(callback: CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    await send_main_menu(callback, state, data_services)
    return await send_message(
        callback.message,
        Msg.PREMIUM_EXPIRED_SHORT.text
    )

#===============================================================================================================================================
# request data from user
@MENU_ROUTER.callback_query(ProductCallback.filter(), States.CHOICE)
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

    if bool(callback_data.is_subscriber) and not await data_services.is_user_has_active_subscription(callback.message.chat.id):
        return await update_main_mune(callback, state, data_services)
        
    
    product_id = callback_data.product_id
    category = callback_data.category

    if category in (CAT_SUBSCRIPTION, CAT_MICROTRANSACTION):
        await state.clear()
        await state.update_data(
            product_id=product_id,
            fact_price=callback_data.fact_price,
            is_subscriber=callback_data.is_subscriber 
        )

        if category == CAT_SUBSCRIPTION:
            return await handle_product_click(callback.message, state, data_services)

        prompt_text = REQUEST_MESSAGES.get(product_id, Msg.WAITING_FOR_SERVICE.text)
        return await send_message(
            message=callback.message,
            mes_text=prompt_text,
            state=state,
            new_state=States.REQUEST_DATA,
            reply_markup=CANCEL
        )
    
    if await is_having_prediction_today(data_services, callback.message.chat.id, product_id):
        return await send_message(
            callback.message,
            Msg.SERVICE_HAS_ALREADY_BEEN_USED.text,
            state, 
            States.MENU,
            OPEN_MENU
        )

    await send_waiting_message(callback.message, state, Msg.WAITING_FOR_SERVICE.text)
    try:
        now = datetime.now()
        tran_dto = TransactionDTO(
            user_id=callback.message.chat.id,
            product_str_id=product_id,
            date_transaction=now.date(),
            time_transaction=now.time(),
            stars_price_actual=callback_data.fact_price,
            token=None,
            is_subscription_active=bool(int(callback_data.is_subscriber))
        )
        return await handle_user_request(
            callback.message, state, predictor, scheduler, pdf_queue, data_services, tran_dto
        )    
    except Exception as e:
        LOG.error(f"Prediction request failed: {e}")
        return await failed_send_prediction(callback.message, state, None)


@MENU_ROUTER.message(F.text, States.REQUEST_DATA)
async def save_request_data(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    temp_data = await state.get_data()
    product_id = temp_data.get("product_id")

    if not await is_valid_data_for_prediction(message.text, product_id):
        LOG.info(f"Invalid data format for {product_id} from user {message.from_user.id}")
        return await send_message(message, Msg.FAILED_DATA_FOR_PREDICTION.text)
    
    await state.update_data(data_for_prediction=message.text)
    await handle_product_click(message, state, data_services)


async def is_having_prediction_today(data_services: DataServices, user_id: int, type_str: str) -> bool:
    pred_dto = GetPredictionDTO(
        user_id,
        datetime.now().date(),
        type_str
    )
    return await data_services.is_having_prediction(pred_dto)


#===============================================================================================================================================
# handle payments
async def handle_product_click(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    try:
        data = await state.get_data()
        product = await data_services.get_product(data["product_id"])
        
        payload = f"{data['product_id']}:{data['is_subscriber']}"
        
        fact_price = data["fact_price"]
        if message.chat.id in ADMINS:
            fact_price = PRICE_FOR_ADMINS
        prices = [LabeledPrice(label=product["name"], amount=fact_price)]

        await state.set_state(States.CONFIRM_PAYMENT)
        if data['product_id'] == PROD_MONTHLY_SUB:
            await send_message(
                message,
                Msg.PROMOTION_SUBSCRIPTION.text
            )
        return await message.answer_invoice(
            title=product["name"],
            description=product["description"],
            prices=prices,
            payload=payload,
            currency=CURRENCY,
            provider_token="",
            reply_markup=PAY
        )
    except Exception as e:
        LOG.error(f"Invoice sending failed: {e}")
        return await send_message(
            message, Msg.FAILED_ANSWER_INVOICE.text, state, States.MENU, OPEN_MENU
        )


@MENU_ROUTER.pre_checkout_query(States.CONFIRM_PAYMENT)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    LOG.info(f"Pre-checkout received from {pre_checkout_query.from_user.id}")
    await pre_checkout_query.answer(ok=True)


@MENU_ROUTER.message(F.successful_payment, States.CONFIRM_PAYMENT, flags={"skip_chat_action": True})
async def process_successful_payment(
    message: Message, 
    state: FSMContext, 
    predictor: Predictor, 
    scheduler: AsyncIOScheduler,
    pdf_queue: Queue, 
    data_services: DataServices
) -> Message:
    await message.delete()
    payment = message.successful_payment
    user_id = message.chat.id
    
    payload_parts = payment.invoice_payload.split(":")
    product_id = payload_parts[0]
    is_sub_val = bool(int(payload_parts[1]))

    LOG.info(f"Payment success: {payment.total_amount} Stars from {user_id} for {product_id}")
    try:
        tran_dto = TransactionDTO(
            user_id,
            product_id,
            datetime.now().date(),
            datetime.now().time(),
            payment.total_amount,
            payment.telegram_payment_charge_id,
            is_sub_val
        )

        temp_data = None
        if product_id != PROD_MONTHLY_SUB:
            await send_waiting_message(message, state, Msg.WAITING_FOR_PREDICTION.text)
            temp_data = await state.get_data()
            await state.clear()

        await handle_user_request(
            message, state, predictor, scheduler, pdf_queue, data_services, tran_dto,
            data=temp_data.get("data_for_prediction") if temp_data else None
        )
    except Exception as e:
        LOG.error(f"Processing payment request failed: {e}")
        refund = partial(refund_payment_by_charge_id, message.bot, user_id, payment.telegram_payment_charge_id, data_services)
        await failed_send_prediction(message, state, refund)
    
    if message.chat.id in ADMINS:
        try:
            await refund_payment_by_charge_id(message.bot, user_id, payment.telegram_payment_charge_id, data_services)
        except Exception as e:
            LOG.error(f"Auto-refund failed: {e}")


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
    if tran_dto.product_str_id == PROD_MONTHLY_SUB:
        await data_services.handle_purchase(tran_dto)
        return await send_message(
            message, 
            Msg.SECCESSFUL_SUBSCRIPTION_PURCHASE.text, 
            state, 
            States.MENU, 
            OPEN_MENU, FIRE_MESSAGE_EFFECT_ID
        )

    product = await data_services.get_product(tran_dto.product_str_id)
    category = product["category"]
    
    gen_result = await predictor.generate_prediction(tran_dto.user_id, tran_dto.product_str_id, **kwargs)
    if not gen_result["success"]:
        LOG.error(f"Predictor failed for {tran_dto.product_str_id}")
        raise RuntimeError("Generation failed")
    
    pred_dto = PredictionDTO(
        tran_dto.user_id, 
        tran_dto.date_transaction,
        None,
        gen_result["type"],
        gen_result["category"],
        gen_result["prediction"],
        gen_result["success"],
        ",".join(card[1] for card in gen_result["cards"]),
        gen_result["pdf"]
    )
    
    tran_id, pred_id = await data_services.handle_purchase(tran_dto, pred_dto)
    
    if category == CAT_MICROTRANSACTION:
        refund = partial(refund_payment_by_charge_id, message.bot, message.chat.id, tran_dto.token, data_services)
        filename = f"{message.from_user.username}_{product['name'].replace(' ', '_')}_{pred_dto.prediction_date}_{tran_id}_{pred_id}"
        
        await pdf_queue.put((
            pred_id, filename, scheduler, send_prediction,
            [message, state, States.MENU, OPEN_MENU],
            failed_send_prediction, [message, state, refund]
        ))
        LOG.info(f"Microtransaction queued for PDF: {pred_id}")
    elif category in (CAT_FREE_SERVICE, CAT_SUB_SERVICE):
        prediction = await data_services.get_prediction_by_id(pred_id)
        if DEBUG:
            wait_time = DEBUG_WAIT
        else:
            wait_time = random.randint(product["min_generate_seconds"], product["max_generate_seconds"])
        create_delayed_message(
            scheduler, send_service, timedelta(seconds=wait_time),
            [message, state, prediction, get_service_mess_kb(pred_id, 1)]
        )
        LOG.info(f"Service message scheduled: {pred_id}")
    else:
        LOG.error(f"Invalid product category: {category}")
        raise TypeError("Unknown category")


async def send_waiting_message(message: Message, state: FSMContext, msg: str) -> Message:
    return await send_message(
        message, 
        msg, 
        state, 
        States.WAITING_PREDICTION
    )


@MENU_ROUTER.callback_query(ServiceMessageData.filter())
async def update_service_message(callback: CallbackQuery, callback_data: ServiceMessageData, data_services: DataServices) -> None:
    await callback.answer("")
    try:
        prediction_record = await data_services.get_prediction_by_id(int(callback_data.prediction_id))
        pred_data = json.loads(prediction_record["prediction"]) 

        all_steps = int(pred_data["steps"])
        current = int(callback_data.current_step)
        next_step = current + (1 if bool(int(callback_data.next)) else -1)
        next_step = max(1, min(next_step, all_steps))

        if not bool(int(pred_data["full"])) and bool(int(callback_data.next)) and current == all_steps:
            msg_text = Msg.PROMOTION_SUBSCRIPTION.text
        elif next_step != current:
            msg_text = Msg.SERVICE.format(
                title=pred_data.get("title", "Прогноз"),
                date=datetime.now().date(),
                topic=pred_data.get(f"topic_{next_step}"),
                prediction=pred_data.get(f"prediction_{next_step}")
            )
        else:
            return

        await callback.message.edit_text(
            text=msg_text,
            reply_markup=get_service_mess_kb(prediction_record["id"], next_step),
            parse_mode="HTML"
        )
    except Exception as e:
        LOG.error(f"Service message update failed: {e}")


#===============================================================================================================================================
# fail handlers
async def failed_send_prediction(message: Message, state: FSMContext, refund_method: Any) -> Message:
    LOG.error(f"Handling prediction failure for user {message.chat.id}")
    if refund_method:
        await refund_method()
    return await send_message(message, Msg.FAILED_PREDICTION_REFUND.text, state, States.MENU, OPEN_MENU)


@MENU_ROUTER.callback_query(
    or_f(
        and_f(F.data == CANCEL_PAY_CALLBACK_DATA, States.CONFIRM_PAYMENT),
        and_f(F.data == CANCEL_CALLBACK_DATA, States.REQUEST_DATA)
    )
)
async def payment_cancel(event: CallbackQuery | Message, state: FSMContext, data_services: DataServices) -> Message:
    LOG.info(f"Operation cancelled by user {event.from_user.id}")
    message = event if isinstance(event, Message) else event.message
    
    if isinstance(event, CallbackQuery):
        await event.answer("")
    
    await message.delete()
    await state.set_state(States.MENU)
    return await send_main_menu(message, state, data_services)