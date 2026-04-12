import logging
from logging import Logger
from typing import Final
from aiogram import Bot

from database.data_services import DataServices

LOG: Final[Logger] = logging.getLogger(__name__)


async def refund_payment(bot: Bot, user_id: int, charge_id: str) -> bool:
    try:
        await bot.refund_star_payment(
            user_id=user_id, 
            telegram_payment_charge_id=charge_id
        )
        LOG.inf(f"Refund successful: User {user_id}, Charge {charge_id}")
        return True
    except Exception as e:
        LOG.error(f"Refund execution error: {e}")
        return False


async def refund_payment_by_charge_id(bot: Bot, user_id: int, charge_id: str, data_services: DataServices) -> bool:
    if not await refund_payment(bot, user_id, charge_id):
        return False
        
    try:
        await data_services.mark_transaction_as_refund_by_token(charge_id)
        return True
    except Exception as e:
        LOG.error(f"DB update failed for charge {charge_id}: {e}")
    
    return False    


async def refund_payment_by_transaction_id(bot: Bot, transaction_id: int, data_services: DataServices) -> bool:
    try:
        transaction = data_services.get_transaction(transaction_id) 
        
        is_refunded = await refund_payment(
            bot=bot, 
            user_id=transaction["user_id"], 
            charge_id=transaction["token"]
        )
        
        if is_refunded:
            await data_services.mark_transaction_as_refund_by_id(transaction_id)
            return True    
    except Exception as e:
        LOG.error(f"Process failed for transaction {transaction_id}: {e}")
    
    return False