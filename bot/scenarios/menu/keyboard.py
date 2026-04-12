from typing import Final

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.data_services import DataServices
from aiogram.filters.callback_data import CallbackData

from common.constants import SUBSCRIBE_DISCOUNT
from lexicon.vocabulary import Buttons


CANCEL_CALLBACK_DATA: Final[str] = "cancel"
CANCEL: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=Buttons.CANCEL.text, callback_data=CANCEL_CALLBACK_DATA)]
    ]
)


CANCEL_PAY_CALLBACK_DATA: Final[str] = "payment_cancel"
PAY: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=Buttons.PAY.text, pay=True)],
        [InlineKeyboardButton(text=Buttons.CANCEL.text, callback_data=CANCEL_PAY_CALLBACK_DATA)]
    ]
)


OPEN_MENU_CALLBACK_DATA: Final[str] = "open_menu"
OPEN_MENU: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=Buttons.OPEN_MENU.text, callback_data=OPEN_MENU_CALLBACK_DATA)]
    ]
)


class ProductCallback(CallbackData, prefix="prod"):
    product_id: str
    category: str
    fact_price: int
    is_subscriber: int


async def get_menu_kb(data_services: DataServices, user_id: int) -> InlineKeyboardMarkup:
    products = await data_services.get_all_product()
    is_subscribed = await data_services.is_user_has_active_subscription(user_id)
    
    builder = InlineKeyboardBuilder()    
    allowed_categories = ({"subscription_service", "microtransaction"} if is_subscribed else {"free_service", "subscription", "microtransaction"})

    for p in products:
        if p["category"] not in allowed_categories:
            continue

        try:
            price = int(p.get('price_stars', 0))
        except (ValueError, TypeError):
            price = 0

        
        if price > 0: 
            price = int(price * SUBSCRIBE_DISCOUNT) if is_subscribed else price
            button_text = Buttons.PRODUCT_BATTON_WITH_PRICE.text.format(text=p["name"], price=price)
        else:
            button_text = Buttons.PRODUCT_BATTON_WITHOUT_PRICE.text.format(text=p["name"])

        builder.button(
            text=button_text,
            callback_data=ProductCallback(
                product_id=p["str_id"],
                category=p["category"],
                fact_price=price,
                is_subscriber=int(is_subscribed)
            )
        )

    builder.adjust(1)
    return builder.as_markup()


class ServiceMessageData(CallbackData, prefix="prod"):
    prediction_id: int
    current_step: int
    next: int


def get_service_mess_kb(prediction_id: int, current_step: int) -> InlineKeyboardMarkup:
    next_callback = ServiceMessageData(
        prediction_id=prediction_id,
        current_step=current_step,
        next=1).pack()
    back_callback = ServiceMessageData(
        prediction_id=prediction_id,
        current_step=current_step,
        next=0).pack()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=Buttons.BACK.text, callback_data=back_callback), InlineKeyboardButton(text=Buttons.NEXT.text, callback_data=next_callback)],
            [InlineKeyboardButton(text=Buttons.OPEN_MENU.text, callback_data=OPEN_MENU_CALLBACK_DATA)]
        ]
    )
