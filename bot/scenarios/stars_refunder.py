import logging
from logging import Logger
from typing import Final
from aiogram import Bot

from database.data_services import DataServices


LOG: Final[Logger] = logging.getLogger(__name__)


async def refund_payment_by_charge_id(bot: Bot, user_id: int, charge_id: str, data_services: DataServices) -> bool:
    try:
        status = await refund_payment(bot, user_id, charge_id)
        if status:
            await data_services.mark_transaction_as_refund_by_token(charge_id)
            return status
    except Exception as e:
        LOG.error(f"Error mark transaction as refund: {e}")
    
    return False    

async def refund_payment_by_transaction_id(bot: Bot, transasction_id: int, data_services: DataServices) -> bool:
    try:
        transasction = data_services.get_transaction(transasction_id)
        status = await refund_payment(bot, transasction["user_id"], transasction["token"])
        if status:
            await data_services.mark_transaction_as_refund_by_id(transasction_id)
            return status    
    except Exception as e:
        LOG.error(f"Error mark transaction as refund: {e}")
    
    return False

async def refund_payment(bot: Bot, user_id: int, charge_id: str) -> bool:
    try:
        await bot.refund_star_payment(
            user_id=user_id, 
            telegram_payment_charge_id=charge_id
        )
        LOG.info(f"Payment {charge_id} successfully returned user with id = {user_id}")
        return True
    except Exception as e:
        LOG.error(f"Error returned payment: {e}")
        return False