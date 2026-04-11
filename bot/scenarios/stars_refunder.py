import logging
from logging import Logger
from typing import Final
from aiogram import Bot

from database.data_services import DataServices


LOG: Final[Logger] = logging.getLogger(__name__)


async def refund_payment(bot: Bot, user_id: int, charge_id: str, data_services: DataServices = None, transasction_id: int = None) -> bool:
    try:
        await bot.refund_star_payment(
            user_id=user_id, 
            telegram_payment_charge_id=charge_id
        )
        if transasction_id and data_services:
            await data_services.mark_transaction_as_refund(transasction_id)
        LOG.info(f"Payment {charge_id} successfully returned user with id = {user_id}")
        return True
    except Exception as e:
        LOG.error(f"Error returned payment: {e}")
        return False