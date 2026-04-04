from asyncpg import Pool

from database.DTO.transaction_dto import TransactionDTO
from database.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def add_new_transaction(self, transaction: TransactionDTO) -> int:
        query = "call api.add_transaction($1, $2, $3, $4, $5, $6, $7, $8, $9)"

        transaction_id = await self._pool.fetchval(
            query,
            transaction.user_id,
            transaction.product_str_id,
            transaction.date_transaction,
            transaction.time_transaction,
            transaction.stars_price_original,
            transaction.stars_price_actual,
            transaction.token,
            transaction.is_subscription_active,
            None
        )
        return transaction_id
