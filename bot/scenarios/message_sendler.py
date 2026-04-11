from datetime import datetime, timedelta
import logging
from logging import Logger
from typing import Any, Final, Callable
from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from scenarios.fsm_states import States
from apscheduler.schedulers.asyncio import AsyncIOScheduler


LOG: Final[Logger] = logging.getLogger(__name__)


async def send_message(message: Message, mes_text: str, state: FSMContext = None, newState: States = None, reply_markup: ReplyKeyboardMarkup = None) -> Message:
    LOG.info(f"Send message: {mes_text[:50]}")
    response = await message.answer(mes_text,
                                    reply_markup=reply_markup)

    if state and newState:
        await state.set_state(newState)

    return response

async def send_prediction(message: Message, state: FSMContext, prediction_id: int, path_ro_pdf: str):
    pass


def create_delayed_message(scheduler: AsyncIOScheduler, delayed_message_method: Callable, delta: timedelta, args: list[Any]) -> None:
    scheduler.add_job(
        delayed_message_method, 
        trigger='date', 
        run_date=datetime.now() + delta,
        args=args
    )