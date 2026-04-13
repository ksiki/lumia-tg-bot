from typing import Final

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from lexicon.vocabulary import Buttons


CHANGE_CALLBACK_DATA: Final[str] = "change_date"
MENU_CALLBACK_DATA: Final[str] = "cancel"
SETTINGS: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=Buttons.CHANGE_DATA.text, callback_data=CHANGE_CALLBACK_DATA)],
        [InlineKeyboardButton(text=Buttons.OPEN_MENU.text, callback_data=MENU_CALLBACK_DATA)]
    ]
)