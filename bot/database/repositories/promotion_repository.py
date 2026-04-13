from asyncpg import Pool

from database.repositories.base_repository import BaseRepository


class PromotionRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def get_text_promotion(self) -> str:
        query = "select * from api.get_text_promotion()"

        return await self._pool.fetchval(query)