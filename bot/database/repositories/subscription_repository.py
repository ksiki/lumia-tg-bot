from asyncpg import Pool, Record

from database.DTO.subscription_dto import SubscriptionDTO
from database.repositories.base_repository import BaseRepository


class SubscriptionRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def add_new_subscription(self, subscription: SubscriptionDTO) -> None:
        query = "call api.add_subscription($1, $2, $3, $4, $5, $6)"

        await self._pool.execute(
            query,
            subscription.user_id,
            subscription.transaction_id,
            subscription.start_date,
            subscription.end_date,
            subscription.created_at_time,
            subscription.status
        )

    async def get_active_subscription(self, user_id: int) -> Record | None:
        query = """ 
            select *
            from mart.v_active_subscription vas
            where user_id = $1
            limit 1
        """

        subscription = await self._pool.fetchrow(
            query,
            user_id
        )
        return subscription

    async def get_last_subscription(self, user_id: int) -> Record | None:
        query = "select * from api.get_last_subscription($1)"

        subscription = await self._pool.fetchrow(
            query,
            user_id
        )
        return subscription

    async def exists_active_subscription(self, user_id: int) -> bool:
        query = """ 
            select exists(
                select 1
                from mart.v_active_subscription vas
                where vas.user_id = $1
            )
        """

        result = await self._pool.fetchval(
            query,
            user_id
        )
        return bool(result)
