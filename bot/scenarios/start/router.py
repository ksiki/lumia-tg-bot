import logging
from datetime import datetime, timedelta
from logging import Logger
from typing import Final

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.DTO import SubscriptionDTO, UserDTO
from database.data_services import DataServices
from lexicon.vocabulary import Buttons, Msg
from middleware import ActionLoggingMiddleware, TypingActionMiddleware
from scenarios.fsm_states import States
from utils.validator import is_valid_date, is_valid_time, is_valid_city
from utils.converter import str_to_date, str_to_time
from scenarios.message_sendler import send_message
from scenarios.menu.router import send_main_menu
from common.constants import FIRE_MESSAGE_EFFECT_ID
from scenarios.start.keyboard import (
    BEGIN_SURVEY, 
    SEX_QUESTION, 
    CONFIRMATION_REGISTRATION, 
    ACTIVATING_GIFT
)


TRIAL_SUBSCRIPTION_DAYS: Final[int] = 3
SUBSCRIPTION_TYPE_TRIAL: Final[str] = "trial"
SEX_MAP: Final[dict[str, str]] = {
    Buttons.GIRL.text: "Девушка",
    Buttons.MAN.text: "Парень"
}

START_ROUTER: Final[Router] = Router()
START_ROUTER.message.middleware(ActionLoggingMiddleware())
START_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


@START_ROUTER.message(CommandStart())
async def start(message: Message, state: FSMContext, data_services: DataServices) -> Message | None:
    await state.clear()
    user_id = message.from_user.id

    try: 
        is_register = await data_services.is_user_registered(user_id)
    except Exception as e:
        LOG.error(f"Registration check failed for {user_id}: {e}")
        is_register = False      
    
    if is_register:
        LOG.info(f"Registered user {user_id} returned")
        return await send_main_menu(message, state, data_services)

    LOG.info(f"New user {user_id} started survey")
    return await send_message(
        message,
        Msg.START_MESSAGE.format(username=message.from_user.username),
        state,
        States.WHATS_YOUR_NAME,
        BEGIN_SURVEY
    )


@START_ROUTER.message(F.text == Buttons.START_ACQUAINTANCE.text, States.WHATS_YOUR_NAME)
async def whats_your_name(message: Message, state: FSMContext) -> Message:
    return await send_message(
        message,
        Msg.WHATS_YOUR_NAME_QUESTION.text,
        state,
        States.YOUR_GIRL_OR_MAN
    )


@START_ROUTER.message(F.text, States.YOUR_GIRL_OR_MAN)
async def whats_your_sex(message: Message, state: FSMContext) -> Message:
    await state.update_data(name=message.text)
    return await send_message(
        message,
        Msg.YOUR_GIRL_OR_MAN_QUESTION.text,
        state,
        States.WHEN_YOUR_BIRTHDAY,
        SEX_QUESTION
    )


@START_ROUTER.message(F.text.in_([Buttons.GIRL.text, Buttons.MAN.text]), States.WHEN_YOUR_BIRTHDAY)
async def whats_your_birthday(message: Message, state: FSMContext) -> Message:
    sex_label = SEX_MAP.get(message.text, "Не указан")
    await state.update_data(sex=sex_label)

    return await send_message(
        message,
        Msg.WHEN_YOUR_BIRTHDAY_QUESTION.text,
        state,
        States.TIME_YOUR_BIRTH
    )


@START_ROUTER.message(F.text, States.TIME_YOUR_BIRTH)
async def whats_your_birth_time(message: Message, state: FSMContext) -> Message:
    if not is_valid_date(message.text):
        LOG.info(f"Invalid birthday input: {message.text}")
        return await send_message(message, Msg.NOT_VALID_WHEN_YOUR_BIRTHDAY_QUESTION.text)

    await state.update_data(birthday=message.text)
    return await send_message(
        message,
        Msg.TIME_YOUR_BIRTH_QUESTION.text,
        state,
        States.YOUR_CITY_BIRTH
    )


@START_ROUTER.message(F.text, States.YOUR_CITY_BIRTH)
async def whats_your_birth_city(message: Message, state: FSMContext) -> Message:
    if not is_valid_time(message.text):
        LOG.info(f"Invalid birth time input: {message.text}")
        return await send_message(message, Msg.NOT_VALID_TIME_YOUR_BIRTH_QUESTION.text)

    await state.update_data(birth_time=message.text)
    return await send_message(
        message,
        Msg.YOUR_CITY_BIRTH_QUESTION.text,
        state,
        States.YOUR_CITY_RESIDENCE
    )


@START_ROUTER.message(F.text, States.YOUR_CITY_RESIDENCE)
async def whats_your_residence_city(message: Message, state: FSMContext) -> Message:
    city_data = await is_valid_city(message.text)
    if not city_data:
        LOG.info(f"Invalid birth city: {message.text}")
        return await send_message(message, Msg.NOT_VALID_YOUR_CITY_QUESTION.text)

    await state.update_data(
        birth_city=city_data.get("city"),
        birth_timezone=city_data.get("timezone")
    )
    return await send_message(
        message,
        Msg.YOUR_CITY_RESIDENCE_QUESTION.text,
        state,
        States.SUCCESSFUL_ACQUAINTANCE
    )


@START_ROUTER.message(F.text, States.SUCCESSFUL_ACQUAINTANCE)
async def successful_registration(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    city_data = await is_valid_city(message.text)
    if not city_data:
        LOG.info(f"Invalid residence city: {message.text}")
        return await send_message(message, Msg.NOT_VALID_YOUR_CITY_QUESTION.text)

    user_data = await state.get_data()
    
    user_dto = UserDTO(
        user_id=message.from_user.id,
        name=user_data.get("name"),
        sex=user_data.get("sex"),
        birthday=str_to_date(user_data.get("birthday")),
        birth_time=str_to_time(user_data.get("birth_time")),
        birth_city=user_data.get("birth_city"),
        birthday_city_timezone=user_data.get("birth_timezone"),
        residence_city=city_data.get("city"),
        residence_city_timezone=city_data.get("timezone"),
        registration_date=datetime.now().date()
    )
    
    await data_services.register_user(user_dto)
    LOG.info(f"User {message.from_user.id} registered successfully")

    return await send_message(
        message,
        Msg.SUCCESSFUL_REGISTRATION.text,
        state,
        States.PREMIUM_GIFT_THREE_DAYS,
        CONFIRMATION_REGISTRATION
    )


@START_ROUTER.message(F.text == Buttons.NEXT.text, States.PREMIUM_GIFT_THREE_DAYS)
async def activate_gift(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    user_id = message.from_user.id
    await state.clear()
    await state.set_state(States.MENU)

    try:
        now = datetime.now()
        sub_dto = SubscriptionDTO(
            user_id=user_id,
            transaction_id=None,
            start_date=now.date(),
            end_date=now.date() + timedelta(days=TRIAL_SUBSCRIPTION_DAYS),
            created_at_time=now.time(),
            status=SUBSCRIPTION_TYPE_TRIAL
        )
        await data_services.add_new_subscription(sub_dto)
        LOG.info(f"Trial activated for {user_id}")
    except Exception as e:
        LOG.error(f"Failed to activate trial for {user_id}: {e}")
    finally:
        response = await send_message(
            message,
            Msg.PREMIUM_GIFT_THREE_DAYS.text,
            reply_markup=ACTIVATING_GIFT,
            message_effect_id=FIRE_MESSAGE_EFFECT_ID
        )
    return response