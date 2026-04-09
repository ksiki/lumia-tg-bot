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

    async def get_product_id_by_str_id(self, str_id: str) -> int | None:
        query = "select api.get_product_id_by_str_id($1)"

        id = await self._pool.fetchval(query, str_id)
        return id
    
    async def get_all_product(self) -> list[Record] | None:
        query = "select * from mart.v_product vp"

        products = await self._pool.fetch(query)
        return products