from aiogram.types import InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.data_services import DataServices
from aiogram.filters.callback_data import CallbackData

from common.constants import SUBSCRIBE_DISCOUNT
from lexicon.vocabulary import Buttons


class ProductCallback(CallbackData, prefix="prod"):
    product_id: str


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
            display_price = price * SUBSCRIBE_DISCOUNT if is_subscribed else price
            button_text = Buttons.PRODUCT_BATTON_WITH_PRICE.text.format(text=p["name"], price=display_price)
        else:
            button_text = Buttons.PRODUCT_BATTON_WITHOUT_PRICE.text.format(text=p["name"])

        builder.button(
            text=button_text, 
            callback_data=ProductCallback(product_id=p["str_id"])
        )

    builder.adjust(1)
    return builder.as_markup()
