from asyncpg import Pool, Record

from database.repositories.base_repository import BaseRepository
from database.DTO.user_dto import UserDTO


class UserRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def get_actual_data(self, user_id: int) -> Record | None:
        query = """
            select
                *
            from mart.v_user_current vuc
            where vuc.user_id = $1::bigint
        """

        data = await self._pool.fetchrow(query, user_id)
        return data

    async def exists(self, user_id: int) -> bool:
        query = """
            select exists(
                select 1
                from mart.v_user_current vuc
                where vuc.user_id = $1
            )
        """

        result = await self._pool.fetchval(query, user_id)
        return bool(result)

    async def add_new_user(self, user: UserDTO) -> None:
        query = "call api.add_new_user($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)"

        await self._pool.execute(
            query,
            user.user_id, 
            user.name, 
            user.sex, 
            user.birthday,
            user.birth_time, 
            user.birth_city, 
            user.birthday_city_timezone,
            user.residence_city, 
            user.residence_city_timezone, 
            user.registration_date
        )

    async def update_user(self, user: UserDTO) -> None:
        query = "call api.update_user_data($1, $2, $3, $4, $5, $6, $7, $8, $9)"

        await self._pool.execute(
            query,
            user.user_id, 
            user.name, 
            user.sex, 
            user.birthday,
            user.birth_time, 
            user.birth_city, 
            user.birthday_city_timezone,
            user.residence_city, 
            user.residence_city_timezone
        )
