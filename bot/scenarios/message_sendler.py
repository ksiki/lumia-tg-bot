import json
import logging
from datetime import datetime, timedelta
from logging import Logger
from typing import Any, Final

from aiogram.types import (
    FSInputFile, 
    InlineKeyboardMarkup, 
    InputMediaPhoto, 
    Message, 
    ReplyKeyboardMarkup
)
from aiogram.fsm.context import FSMContext
from asyncpg import Record
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from lexicon.vocabulary import Msg
from scenarios.fsm_states import States

LOG: Final[Logger] = logging.getLogger(__name__)
CARDS_CAPTION: Final[str] = "✨ Выпавшие карты"
CARDS_SEPARATOR: Final[str] = ","
JOB_TRIGGER_DATE: Final[str] = "date"


async def send_message(
    message: Message, 
    mes_text: str, 
    state: FSMContext = None, 
    new_state: States = None, 
    reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup = None, 
    message_effect_id: str = None
) -> Message:
    LOG.info(f"Sending message to user {message.from_user.id}")
    
    response = await message.answer(
        text=mes_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        message_effect_id=message_effect_id
    )

    if state and new_state:
        await state.set_state(new_state)

    return response


async def send_prediction(
    message: Message, 
    state: FSMContext, 
    new_state: States, 
    reply_markup: InlineKeyboardMarkup, 
    prediction: Record, 
    path_to_pdf: str
) -> Message:
    LOG.info(f"Sending prediction PDF to user {message.from_user.id}")
    
    await send_cards(message, prediction["cards"])

    document = FSInputFile(path_to_pdf)
    await state.set_state(new_state)
    
    return await message.answer_document(
        document=document,
        caption=Msg.PREDICTION.text,
        reply_markup=reply_markup
    )


async def send_service(
    message: Message, 
    state: FSMContext, 
    prediction: Record, 
    reply_markup: InlineKeyboardMarkup
) -> Message:
    LOG.info(f"Formatting service message for user {message.from_user.id}")
    
    prediction_data = json.loads(prediction["prediction"])
    
    formatted_text = Msg.SERVICE.format(
        title=prediction_data["title"],
        date=datetime.now().date(),
        topic=prediction_data["topic_1"],
        prediction=prediction_data["prediction_1"]
    )
        
    await send_cards(message, prediction["cards"])
    
    return await send_message(
        message=message,
        mes_text=formatted_text,
        state=state,
        new_state=States.MENU,
        reply_markup=reply_markup
    )


async def send_cards(message: Message, path_to_cards: str | None) -> None:
    if not path_to_cards:
        return
    
    cards_list = path_to_cards.split(CARDS_SEPARATOR)
    if not cards_list:
        return

    media_group = []
    for i, path in enumerate(cards_list):
        photo = InputMediaPhoto(media=FSInputFile(path))
        if i == 0:
            photo.caption = CARDS_CAPTION
        media_group.append(photo)

    try:
        LOG.info(f"Sending media group ({len(media_group)} cards) to {message.from_user.id}")
        await message.answer_media_group(media=media_group)
    except Exception as e:
        LOG.error(f"Failed to send media group: {e}")


def create_delayed_message(
    scheduler: AsyncIOScheduler, 
    delayed_message_method: Any, 
    delta: timedelta, 
    args: list[Any]
) -> None:
    run_date = datetime.now(scheduler.timezone) + delta
    
    LOG.info(f"Scheduling delayed task for {run_date}")
    
    scheduler.add_job(
        func=delayed_message_method, 
        trigger=JOB_TRIGGER_DATE, 
        run_date=run_date,
        args=args
    )