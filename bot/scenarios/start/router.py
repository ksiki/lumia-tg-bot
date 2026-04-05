import logging
from logging import Logger
from typing import Final
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup

from lexicon.vocabulary import Buttons
from lexicon.vocabulary import Msg
from middleware.action_logging_middleware import ActionLoggingMiddleware
from middleware.text_message import TypingActionMiddleware
from utils.validator import is_valid_date, is_valid_time, is_valid_city
from scenarios.start.fsm_states import States
from scenarios.start.keyboard import BEGIN_SURVEY, SEX_QUESTION, CONFIRMATION_REGISTRATION, ACTIVATING_GIFT


START_ROUTER: Final[Router] = Router()
START_ROUTER.message.middleware(ActionLoggingMiddleware())
START_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


async def send_message(message: Message, mes_text: str, state: FSMContext = None, newState: States = None, reply_markup: ReplyKeyboardMarkup = None) -> Message:
    response = await message.answer(mes_text,
                                    reply_markup=reply_markup)

    if state and newState:
        await state.set_state(newState)

    return response


@START_ROUTER.message(CommandStart())
async def start(message: Message, state: FSMContext) -> Message:
    await state.clear()

    LOG.info("Command /start: Start message")
    return await send_message(message,
                              Msg.START_MESSAGE.format(username=message.from_user.username),
                              state,
                              States.WHATS_YOUR_NAME,
                              BEGIN_SURVEY)


@START_ROUTER.message(F.text == Buttons.START_ACQUAINTANCE.text, States.WHATS_YOUR_NAME)
async def whats_your_name(message: Message, state: FSMContext) -> Message:
    LOG.info("Question: Whats your name")
    return await send_message(message,
                              Msg.WHATS_YOUR_NAME_QUESTION.text,
                              state,
                              States.YOUR_GIRL_OR_MAN)


@START_ROUTER.message(F.text, States.YOUR_GIRL_OR_MAN)
async def whats_your_sex(message: Message, state: FSMContext) -> Message:
    await state.update_data(name=message.text)

    LOG.info("Question: Whats your sex")
    return await send_message(message,
                              Msg.YOUR_GIRL_OR_MAN_QUESTION.text,
                              state,
                              States.WHEN_YOUR_BIRTHDAY,
                              SEX_QUESTION)


@START_ROUTER.message(F.text.in_([Buttons.GIRL.text, Buttons.MAN.text]), States.WHEN_YOUR_BIRTHDAY)
async def whats_your_birthday(message: Message, state: FSMContext) -> Message:
    text = message.text
    sex: str
    if text == Buttons.GIRL.text:
        sex = "Девушка"
    else:
        sex = "Парень"
    await state.update_data(sex=sex)

    LOG.info("Question: Whats your burthday")
    return await send_message(message,
                              Msg.WHEN_YOUR_BIRTHDAY_QUESTION.text,
                              state,
                              States.TIME_YOUR_BIRTH)


@START_ROUTER.message(F.text, States.TIME_YOUR_BIRTH)
async def whats_your_birth_time(message: Message, state: FSMContext) -> Message:
    if not is_valid_date(message.text):
        LOG.info("Attention: Not valid birthday date")
        return await send_message(message,
                                  Msg.NOT_VALID_WHEN_YOUR_BIRTHDAY_QUESTION.text)

    await state.update_data(birthday=message.text)
    LOG.info("Question: Whats your birth time")
    return await send_message(message,
                              Msg.TIME_YOUR_BIRTH_QUESTION.text,
                              state,
                              States.YOUR_CITY_BIRTH)


@START_ROUTER.message(F.text, States.YOUR_CITY_BIRTH)
async def whats_your_birth_city(message: Message, state: FSMContext) -> Message:
    if not is_valid_time(message.text):
        LOG.info("Attention: Not valid birth time")
        return await send_message(message,
                                  Msg.NOT_VALID_TIME_YOUR_BIRTH_QUESTION.text)

    await state.update_data(birth_time=message.text)
    LOG.info("Question: Whats your birth city")
    return await send_message(message,
                              Msg.YOUR_CITY_BIRTH_QUESTION.text,
                              state,
                              States.YOUR_CITY_RESIDENCE)


@START_ROUTER.message(F.text, States.YOUR_CITY_RESIDENCE)
async def whats_your_residence_city(message: Message, state: FSMContext) -> Message:
    city_data: dict[str, str] | None = await is_valid_city(message.text)
    if not city_data:
        LOG.info("Attention: Not valid birth city")
        return await send_message(message,
                                  Msg.NOT_VALID_YOUR_CITY_QUESTION.text)

    await state.update_data(birth_city=city_data.get("city"),
                            birth_timezone=city_data.get("timezone"))
    LOG.info("Question: Whats your residence city")
    return await send_message(message,
                              Msg.YOUR_CITY_RESIDENCE_QUESTION.text,
                              state,
                              States.SUCCESSFUL_ACQUAINTANCE)


@START_ROUTER.message(F.text, States.SUCCESSFUL_ACQUAINTANCE)
async def successful_registration(message: Message, state: FSMContext) -> Message:
    city_data: dict[str, str] | None = await is_valid_city(message.text)
    if not city_data:
        LOG.info("Attention: Not valid residence city")
        return await send_message(message,
                                  Msg.NOT_VALID_YOUR_CITY_QUESTION.text)
    
    await state.update_data(residence_city=city_data.get("city"),
                            residence_timezone=city_data.get("timezone"))

    user_data = await state.get_data()
    answer_message = Msg.SUCCESSFUL_REGISTRATION.format(
        name=user_data.get("name"),
        sex=user_data.get("sex"),
        birthday=user_data.get("birthday"),
        birth_time=user_data.get("birth_time"),
        birth_city=user_data.get("birth_city"),
        residence_city=user_data.get("residence_city")
    )

    LOG.info("Message: Confirmation registration")
    return await send_message(message,
                              answer_message,
                              state,
                              States.PREMIUM_GIFT_FIVE_DAYS,
                              CONFIRMATION_REGISTRATION)


@START_ROUTER.message(F.text == Buttons.FORTH.text, States.PREMIUM_GIFT_FIVE_DAYS)
async def activate_gift(message: Message, state: FSMContext) -> Message:
    user_data = await state.get_data()
    await state.clear()
    
    LOG.info("Gift: Dree premium for 3 days")
    return await send_message(message,
                              Msg.PREMIUM_GIFT_FIVE_DAYS.text,
                              reply_markup=ACTIVATING_GIFT)
