import logging
from logging import Logger
from typing import Final

from asyncpg import Record

from database.DTO.get_prediction_dto import GetPredictionDTO
from database.DTO.prediction_dto import PredictionDTO
from database.DTO.action_log_dto import ActionLogDTO
from database.DTO.subscription_dto import SubscriptionDTO
from database.DTO.transaction_dto import TransactionDTO
from database.DTO.user_dto import UserDTO
from database.repositories.user_repository import UserRepository
from database.repositories.transaction_repository import TransactionRepository
from database.repositories.subscription_repository import SubscriptionRepository
from database.repositories.action_log_repository import ActionLogRepository
from database.repositories.prediction_repository import PredictionRepository
from database.repositories.products_repository import ProductsRepository
from database.common.log_query_decorator import log_query
from database.common.log_all_methods_decorator import log_all_methods


LOG: Final[Logger] = logging.getLogger(__name__)


@log_all_methods(log_query(LOG))
class DataServices:
    def __init__(self, user_rep: UserRepository,
                 transaction_rep: TransactionRepository,
                 subscription_rep: SubscriptionRepository,
                 action_log_rep: ActionLogRepository,
                 prediction_rep: PredictionRepository,
                 products_rep: ProductsRepository
                 ) -> None:
        self.__user_rep = user_rep
        self.__transaction_rep = transaction_rep
        self.__subscription_rep = subscription_rep
        self.__action_log_rep = action_log_rep
        self.__prediction_rep = prediction_rep
        self.__products_rep = products_rep

    async def is_user_registered(self, user_id: int) -> bool:
        response = await self.__user_rep.exists(user_id)
        return response
    
    async def get_user_actual_date(self, user_id: int) -> Record | None:
        response = await self.__user_rep.get_actual_data(user_id)
        return response

    async def is_user_has_active_subscription(self, user_id: int) -> bool:
        response = await self.__subscription_rep.exists_active_subscription(user_id)
        return response

    async def get_subscription(self, user_id: int) -> Record | None:
        response = await self.__subscription_rep.get_subscription(user_id)
        return response
    
    async def get_product(self, str_id: str) -> Record | None:
        response = await self.__products_rep.get_product(str_id)
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
        await self.__subscription_rep.add_new_subscription(subscription_dto)

    async def add_new_action_log(self, action_log_dto: ActionLogDTO) -> None:
        await self.__action_log_rep.add_action_log(action_log_dto)

    async def add_new_prediction(self, prediction_dto: PredictionDTO) -> None:
        await self.__prediction_rep.add_prediction(prediction_dto)
