import logging
from logging import Logger
from typing import Final

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.DTO import UserDTO
from database.data_services import DataServices
from lexicon.vocabulary import Msg
from middleware import ActionLoggingMiddleware, TypingActionMiddleware
from scenarios.fsm_states import States
from scenarios.message_sendler import send_message
from scenarios.menu.router import send_main_menu
from scenarios.menu.keyboard import SETTINGS_CALLBACK_DATA
from scenarios.user_settings.keyboard import (
    SETTINGS, 
    MENU_CALLBACK_DATA, 
    CHANGE_CALLBACK_DATA
)
from utils.converter import str_to_date, str_to_time
from utils.validator import is_valid_city


USER_SETTINGS_ROUTER: Final[Router] = Router()
USER_SETTINGS_ROUTER.message.middleware(ActionLoggingMiddleware())
USER_SETTINGS_ROUTER.message.middleware(TypingActionMiddleware())
LOG: Final[Logger] = logging.getLogger(__name__)


#===============================================================================================================================================
# all settings
@USER_SETTINGS_ROUTER.callback_query(F.data == SETTINGS_CALLBACK_DATA, States.CHOICE)
async def settings_handle(callback: CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    return await send_setting(callback, state, data_services)

async def send_setting(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    if isinstance(event, CallbackQuery):
        await event.answer("")

    message = event if isinstance(event, Message) else event.message
    return await send_message(
        message,
        Msg.SETTINGS.text,
        state,
        States.SETTINGS,
        SETTINGS
    )

@USER_SETTINGS_ROUTER.callback_query(F.data == MENU_CALLBACK_DATA, States.SETTINGS)
async def open_main_menu(event: Message | CallbackQuery, state: FSMContext, data_services: DataServices) -> Message:
    return await send_main_menu(event, state, data_services)


#===============================================================================================================================================
# change user data
@USER_SETTINGS_ROUTER.callback_query(F.data == CHANGE_CALLBACK_DATA, States.SETTINGS)
async def start_changing_user_data(callback: CallbackQuery, state: FSMContext) -> Message:
    await callback.answer("")
    await state.update_data(is_editing=True)
    
    return await send_message(
        callback.message,
        Msg.WHATS_YOUR_NAME_QUESTION.text,
        state,
        States.YOUR_GIRL_OR_MAN
    )


async def is_editing_filter(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    return data.get("is_editing") is True


@USER_SETTINGS_ROUTER.message(F.text, States.SUCCESSFUL_ACQUAINTANCE, is_editing_filter)
async def finish_updating_user_data(message: Message, state: FSMContext, data_services: DataServices) -> Message:
    city_data = await is_valid_city(message.text)
    if not city_data:
        LOG.info(f"Update: Invalid residence city: {message.text}")
        return await send_message(message, Msg.NOT_VALID_YOUR_CITY_QUESTION.text)

    user_data = await state.get_data()
    
    user_dto = UserDTO(
        user_id=message.chat.id,
        name=user_data.get("name"),
        sex=user_data.get("sex"),
        birthday=str_to_date(user_data.get("birthday")),
        birth_time=str_to_time(user_data.get("birth_time")),
        birth_city=user_data.get("birth_city"),
        birthday_city_timezone=user_data.get("birth_timezone"),
        residence_city=city_data.get("city"),
        residence_city_timezone=city_data.get("timezone"),
        registration_date=None
    )

    try:
        await data_services.update_user_date(user_dto)
        LOG.info(f"User {message.from_user.id} updated data successfully")

        await state.clear()
        await state.set_state(States.CHOICE) 
    except Exception as e:
        LOG.error(f"Failed to update user {message.from_user.id}: {e}")
        return await send_message(
            message,
            Msg.FILED_USER_UPDATE.text,
            state,
            States.Menu
        )
    finally:
        await send_main_menu(message, state, data_services)
