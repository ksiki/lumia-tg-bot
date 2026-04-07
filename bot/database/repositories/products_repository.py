from asyncpg import Pool, Record

from database.repositories.base_repository import BaseRepository


class ProductsRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def get_product(self, str_id: str) -> Record | None:
        query = """
            select *
            from mart.v_product vp
            where str_id = $1
        """

        product = await self._pool.fetchrow(query, str_id)
        return product

    async def get_all_product(self) -> list[Record] | None:
        query = "select * from mart.v_product vp"

        products = await self._pool.fetch(query)
        return products