from datetime import date, datetime, timedelta
import logging
from logging import Logger
from typing import Final
from asyncpg import Record

from database.DTO import (
    UserDTO, 
    GetPredictionDTO, 
    PredictionDTO, 
    ActionLogDTO, 
    SubscriptionDTO, 
    TransactionDTO
)
from database.repositories import (
    UserRepository, 
    TransactionRepository, 
    SubscriptionRepository, 
    ActionLogRepository, 
    PredictionRepository, 
    ProductsRepository, 
    CalendarRepository,
    PromotionRepository
)
from common.log_errors_decorator import log_errors
from common.log_all_methods_decorator import log_all_methods
from common.constants import MOUNTLY_SUBSCRIPTION_LENGTH


LOG: Final[Logger] = logging.getLogger(__name__)


@log_all_methods(log_errors(LOG))
class DataServices:
    def __init__(self, pool) -> None:
        self.__pool = pool
        self.__user_rep = UserRepository(self.__pool)
        self.__transaction_rep = TransactionRepository(self.__pool)
        self.__subscription_rep = SubscriptionRepository(self.__pool)
        self.__action_log_rep = ActionLogRepository(self.__pool)
        self.__prediction_rep = PredictionRepository(self.__pool)
        self.__products_rep = ProductsRepository(self.__pool)
        self.__calendar_rep = CalendarRepository(self.__pool)
        self.__promotion_rep = PromotionRepository(self.__pool)        

#===============================================================================================================================================
# calendar
    async def get_week(self, fount_date: date) -> Record | None:
        response = await self.__calendar_rep.get_week(fount_date)
        return response

#===============================================================================================================================================
# promotion
    async def get_text_promotion(self) -> str:
        return await self.__promotion_rep.get_text_promotion()

#===============================================================================================================================================
# user
    async def is_user_registered(self, user_id: int) -> bool:
        response = await self.__user_rep.exists(user_id)
        return response
    
    async def get_user_actual_data(self, user_id: int) -> Record | None:
        response = await self.__user_rep.get_actual_data(user_id)
        return response

    async def is_user_has_active_subscription(self, user_id: int) -> bool:
        response = await self.__subscription_rep.exists_active_subscription(user_id)
        return response
    
    async def register_user(self, user_dto: UserDTO) -> None:
        await self.__user_rep.add_new_user(user_dto)

    async def update_user_date(self, user_dto: UserDTO) -> None:
        await self.__user_rep.update_user(user_dto)

#===============================================================================================================================================
# product
    async def get_product(self, str_id: str) -> Record | None:
        response = await self.__products_rep.get_product(str_id)
        return response

    async def get_product_id_by_str_id(self, str_id: str) -> int | None:
        response = await self.__products_rep.get_product_id_by_str_id(str_id)
        return response

    async def get_all_product(self) -> list[Record] | None:
        response = await self.__products_rep.get_all_product()
        return response

#===============================================================================================================================================
# prediction
    async def get_prediction(self, found_prediction: GetPredictionDTO) -> Record | None:
        response = await self.__prediction_rep.get_prediction(found_prediction)
        return response
    
    async def get_prediction_by_id(self, prediction_id: int) -> Record | None:
        return await self.__prediction_rep.get_prediction_by_id(prediction_id)

    async def is_having_prediction(self, found_prediction: GetPredictionDTO) -> bool:
        return await self.__prediction_rep.is_having_prediction(found_prediction)

    async def add_new_prediction(self, prediction_dto: PredictionDTO) -> int:
        return await self.__prediction_rep.add_prediction(prediction_dto)

#===============================================================================================================================================
# transaction
    async def get_transaction(self, transaction_id: int) -> Record | None:
        return await self.__transaction_rep.get_transaction(transaction_id)

    async def mark_transaction_as_refund_by_id(self, transaction_id: int) ->  None:
        await self.__transaction_rep.mark_transaction_as_refund_by_id(transaction_id)

    async def mark_transaction_as_refund_by_token(self, token: str) ->  None:
        await self.__transaction_rep.mark_transaction_as_refund_by_token(token)

    async def handle_purchase(self, transaction_dto: TransactionDTO, prediction_dto: PredictionDTO = None) -> tuple[int]:
        async with self.__pool.acquire() as connection:
            async with connection.transaction():
                t_id = await self.__transaction_rep.add_new_transaction(connection, transaction_dto)
                p_id = await self.__apply_transaction_benefits(connection, t_id, transaction_dto, prediction_dto)
                return t_id, p_id

    async def __apply_transaction_benefits(self, connection, transaction_id: int, transaction_dto: TransactionDTO, prediction_dto: PredictionDTO = None) -> int:
        if transaction_dto.product_str_id == "monthly_subscription":
            sub_dto = SubscriptionDTO(
                transaction_dto.user_id,
                transaction_id,
                datetime.now().date(),
                datetime.now().date() + timedelta(days=MOUNTLY_SUBSCRIPTION_LENGTH),
                transaction_dto.time_transaction,
                "paid"
            )
            new_sub_dtp = await self.__handle_subscription(sub_dto, connection)
            await self.__subscription_rep.add_new_subscription(new_sub_dtp, connection)
            return -1
        else:
            if not prediction_dto:
                LOG.error("PredictionDTO is null")
                raise TypeError()
            
            new_pred_dto = PredictionDTO(
                prediction_dto.user_id,
                prediction_dto.prediction_date,
                transaction_id,
                prediction_dto.type,
                prediction_dto.category,
                prediction_dto.prediction,
                prediction_dto.success,
                prediction_dto.cards,
                prediction_dto.with_pdf
            )
            return await self.__prediction_rep.add_prediction(new_pred_dto, connection)

#===============================================================================================================================================
# subscription
    async def get_active_subscription(self, user_id: int) -> Record | None:
        response = await self.__subscription_rep.get_active_subscription(user_id)
        return response

    async def get_last_subscription(self, user_id: int) -> Record | None:
        return await self.__subscription_rep.get_last_subscription(user_id)

    async def add_new_subscription(self, subscription_dto: SubscriptionDTO) -> None:
        new_sub_dtp = await self.__handle_subscription(subscription_dto)
        await self.__subscription_rep.add_new_subscription(new_sub_dtp)

    async def __handle_subscription(self, subscription_dto: SubscriptionDTO, connection = None) -> SubscriptionDTO:
        last_sub = await self.__subscription_rep.get_last_subscription(subscription_dto.user_id, connection)
        new_dto = None
        if last_sub and last_sub["end_date"] >= datetime.now().date():
            new_start_date = last_sub["end_date"] + timedelta(days=1)
            new_end_date = new_start_date + (subscription_dto.end_date - subscription_dto.start_date)
            new_dto = SubscriptionDTO(
                subscription_dto.user_id,
                subscription_dto.transaction_id,
                new_start_date,
                new_end_date,
                subscription_dto.created_at_time,
                subscription_dto.status
            )
        return new_dto or subscription_dto
    
#===============================================================================================================================================
# action log
    async def add_new_action_log(self, action_log_dto: ActionLogDTO) -> None:
        await self.__action_log_rep.add_action_log(action_log_dto)
