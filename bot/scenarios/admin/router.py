from argparse import ArgumentError
from datetime import datetime, timedelta
import logging
from logging import Logger
from typing import Final, Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.DTO import SubscriptionDTO
from scenarios.stars_refunder import refund_payment_by_charge_id, refund_payment_by_transaction_id
from lexicon.vocabulary import AdminMsg
from scenarios.message_sendler import send_message
from database.data_services import DataServices
from middleware import ActionLoggingMiddleware, TypingActionMiddleware
from config import ADMINS

LOG: Final[Logger] = logging.getLogger(__name__)

# Admin Commands and Constants
ADMIN_COMMAND: Final[str] = "ad"
ADMIN_GIFT_TYPE: Final[str] = "admin_gift"

CMD_USER: Final[str] = "user"
CMD_USER_SUBS: Final[str] = "usub"
CMD_GIFT_SUB: Final[str] = "giftsub"
CMD_GET_TOKEN: Final[str] = "token"
CMD_REFUND_ID: Final[str] = "idrefund"
CMD_REFUND_TOKEN: Final[str] = "tokenrefund"

ADMIN_ROUTER: Final[Router] = Router()
ADMIN_ROUTER.message.middleware(ActionLoggingMiddleware())
ADMIN_ROUTER.message.middleware(TypingActionMiddleware())


@ADMIN_ROUTER.message(Command(ADMIN_COMMAND))
async def admin_handler(message: Message, data_services: DataServices) -> Message | None:
    user_id = message.chat.id
    if user_id not in ADMINS:
        LOG.info(f"Unauthorized access attempt to admin panel by user {user_id}")
        return

    if not message.text:
        return

    text = message.text.strip()
    command_parts = text.split()

    if len(command_parts) == 1:
        return await send_message(message, AdminMsg.INFO.text)

    try:
        sub_command = command_parts[1]
        LOG.info(f"Admin panel params: {str(command_parts)}")
        match sub_command:
            case str(c) if c == CMD_USER:
                return await user_info(message, data_services, int(command_parts[2]))
            case str(c) if c == CMD_USER_SUBS:
                return await user_subs_info(message, data_services, int(command_parts[2]))
            case str(c) if c == CMD_GIFT_SUB:
                return await gift_subscription(message, data_services, int(command_parts[2]), int(command_parts[3]))
            case str(c) if c == CMD_GET_TOKEN:
                return await get_token(message, data_services, int(command_parts[2]))
            case str(c) if c == CMD_REFUND_ID:
                return await refund_stars_by_tran_id(message, data_services, int(command_parts[2]))
            case str(c) if c == CMD_REFUND_TOKEN:
                return await refund_stars_by_token(message, data_services, command_parts[2])
            case _:
                raise ArgumentError(None, f"Unknown sub-command: {sub_command}")
    except Exception as e:
        LOG.error(f"Admin command execution failed: {e}")
        await send_message(
            message,
            AdminMsg.SOME_ERROR.format(command=text, error=str(e))
        )


async def user_info(message: Message, data_services: DataServices, user_id: int) -> Message | None:
    user_data = await data_services.get_user_actual_data(user_id)
    has_subscription = await data_services.is_user_has_active_subscription(user_id)

    LOG.info(f"Admin requested info for user {user_id}")
    return await send_message(
        message,
        AdminMsg.USER_INFO.format(
           user_id=user_data["user_id"],
           last_version=user_data["version_id"],
           name=user_data["name"],
           sex=user_data["sex"],
           birthday=user_data["birthday"],
           birth_time=user_data["birth_time"],
           birth_city=user_data["birth_city"],
           residence_city=user_data["residence_city"],
           timezone=user_data["timezone"],
           registration_date=user_data["registration_date"],
           has_active_subscription=has_subscription
        )
    )


async def user_subs_info(message: Message, data_services: DataServices, user_id: int) -> Message | None:
    active_sub = await data_services.get_active_subscription(user_id)
    last_sub = await data_services.get_last_subscription(user_id)

    if not active_sub:
        LOG.info(f"Subscription info not found for user {user_id}")
        return await send_message(message, AdminMsg.NOT_FOUND_SUB.format(user_id=user_id))

    return await send_message(
        message,
        AdminMsg.SUBS_INFO.format(
            user_id=user_id,
            a_tran_id=active_sub["transaction_id"],
            a_start_date=active_sub["start_date"],
            a_end_date=active_sub["end_date"],
            a_create_at_time=active_sub["create_at_time"],
            a_status=active_sub["status"],
            l_tran_id=last_sub["transaction_id"],
            l_start_date=last_sub["start_date"],
            l_end_date=last_sub["end_date"],
            l_create_at_time=last_sub["create_at_time"],
            l_status=last_sub["status"]
        )
    )


async def gift_subscription(message: Message, data_services: DataServices, user_id: int, days: int) -> Message | None:
    now = datetime.now()
    sub_dto = SubscriptionDTO(
        user_id=user_id,
        transaction_id=None,
        start_date=now.date(),
        end_date=now.date() + timedelta(days=days),
        created_at_time=now.time(),
        status=ADMIN_GIFT_TYPE
    )
    
    await data_services.add_new_subscription(sub_dto)
    LOG.info(f"Gift subscription ({days} days) granted to user {user_id}")
    return await send_message(message, AdminMsg.SUCCES.text)


async def get_token(message: Message, data_services: DataServices, tran_id: int) -> Message | None:
    transaction = await data_services.get_transaction(tran_id)
    if transaction:
        LOG.info(f"Token retrieved for transaction {tran_id}")
        return await send_message(message, str(transaction["token"] or "Token in transaction is <b>null</b>"))


async def refund_stars_by_tran_id(message: Message, data_services: DataServices, tran_id: int) -> Message | None:
    success = await refund_payment_by_transaction_id(message.bot, tran_id, data_services)
    
    msg_template = AdminMsg.SUCCESS_REFUND_TRAN_ID if success else AdminMsg.FAILED_REFUND_TRAN_ID
    
    if success:
        LOG.info(f"Successful stars refund by transaction ID: {tran_id}")
    else:
        LOG.error(f"Failed stars refund by transaction ID: {tran_id}")

    return await send_message(
        message,
        msg_template.format(user_id=message.chat.id, tran_id=tran_id)
    )


async def refund_stars_by_token(message: Message, data_services: DataServices, token: str) -> Message | None:
    if not token:
        raise ArgumentError(None, "Token is required")
    
    success = await refund_payment_by_charge_id(message.bot, message.chat.id, token, data_services)
    
    msg_template = AdminMsg.SUCCESS_REFUND_TOKEN if success else AdminMsg.FAILED_REFUND_TOKEN

    if success:
        LOG.info(f"Successful stars refund by token: {token}")
    else:
        LOG.error(f"Failed stars refund by token: {token}")

    return await send_message(
        message,
        msg_template.format(user_id=message.chat.id, token=token)
    )