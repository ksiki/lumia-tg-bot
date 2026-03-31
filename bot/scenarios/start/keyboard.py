from typing import Final
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from lexicon.vocabulary import Buttons


BEGIN_SURVEY: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=Buttons.START_ACQUAINTANCE.text)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
SEX_QUESTION: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=Buttons.GIRL.text),
         KeyboardButton(text=Buttons.MAN.text)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
CONFIRMATION_REGISTRATION: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=Buttons.FORTH.text)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
ACTIVATING_GIFT: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=Buttons.ACTIVATE.text)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
