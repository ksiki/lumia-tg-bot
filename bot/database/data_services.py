from datetime import date, timedelta
import logging
from logging import Logger
from typing import Final
from asyncpg import Record

from database.DTO import UserDTO, GetPredictionDTO, PredictionDTO, ActionLogDTO, SubscriptionDTO, TransactionDTO
from database.repositories import UserRepository, TransactionRepository, SubscriptionRepository, ActionLogRepository, PredictionRepository, ProductsRepository, CalendarRepository
from common.log_errors_decorator import log_errors
from common.log_all_methods_decorator import log_all_methods


LOG: Final[Logger] = logging.getLogger(__name__)


@log_all_methods(log_errors(LOG, False))
class DataServices:
    def __init__(self, user_rep: UserRepository,
                 transaction_rep: TransactionRepository,
                 subscription_rep: SubscriptionRepository,
                 action_log_rep: ActionLogRepository,
                 prediction_rep: PredictionRepository,
                 products_rep: ProductsRepository,
                 calendar_rep: CalendarRepository
                 ) -> None:
        self.__user_rep = user_rep
        self.__transaction_rep = transaction_rep
        self.__subscription_rep = subscription_rep
        self.__action_log_rep = action_log_rep
        self.__prediction_rep = prediction_rep
        self.__products_rep = products_rep
        self.__calendar_rep = calendar_rep


    async def is_user_registered(self, user_id: int) -> bool:
        response = await self.__user_rep.exists(user_id)
        return response
    
    async def get_user_actual_data(self, user_id: int) -> Record | None:
        response = await self.__user_rep.get_actual_data(user_id)
        return response
    
    async def get_week(self, fount_date: date) -> Record | None:
        response = await self.__calendar_rep.get_week(fount_date)
        return response

    async def is_user_has_active_subscription(self, user_id: int) -> bool:
        response = await self.__subscription_rep.exists_active_subscription(user_id)
        return response

    async def get_active_subscription(self, user_id: int) -> Record | None:
        response = await self.__subscription_rep.get_active_subscription(user_id)
        return response

    async def get_product(self, str_id: str) -> Record | None:
        response = await self.__products_rep.get_product(str_id)
        return response

    async def get_product_id_by_str_id(self, str_id: str) -> int | None:
        response = await self.__products_rep.get_product_id_by_str_id(str_id)
        return response

    async def get_all_product(self) -> list[Record] | None:
        response = await self.__products_rep.get_all_product()
        return response

    async def get_prediction(self, found_prediction: GetPredictionDTO) -> Record | None:
        response = await self.__prediction_rep.get_prediction(found_prediction)
        return response

    async def register_user(self, user_dto: UserDTO) -> None:
        await self.__user_rep.add_new_user(user_dto)

    async def update_user_date(self, user_dto: UserDTO) -> None:
        await self.__user_rep.add_new_user(user_dto)

    async def add_new_transaction(self, transaction_dto: TransactionDTO) -> int:
        return await self.__transaction_rep.add_new_transaction(transaction_dto)

    async def add_new_subscription(self, subscription_dto: SubscriptionDTO) -> None:
        current_subscription = await self.get_active_subscription(subscription_dto.user_id)

        new_dto = None
        if current_subscription:
            last_sub = await self.__subscription_rep.get_last_subscription(subscription_dto.user_id)
            if not last_sub:
                last_sub = current_subscription
            
            new_start_date = last_sub["end_date"] + timedelta(days=1)
            new_end_date = new_start_date + (subscription_dto.end_date - subscription_dto.start_date)
            new_dto = SubscriptionDTO(
                subscription_dto.user_id,
                subscription_dto.transaction_id,
                new_start_date,
                new_end_date,
                last_sub["created_at_time"],
                subscription_dto.status
            )

        await self.__subscription_rep.add_new_subscription(new_dto if new_dto else subscription_dto)

    async def add_new_action_log(self, action_log_dto: ActionLogDTO) -> None:
        await self.__action_log_rep.add_action_log(action_log_dto)

    async def add_new_prediction(self, prediction_dto: PredictionDTO) -> None:
        await self.__prediction_rep.add_prediction(prediction_dto)
