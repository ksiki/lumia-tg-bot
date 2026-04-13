from datetime import date
from asyncpg import Pool, Record

from database.repositories.base_repository import BaseRepository


class CalendarRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def get_week(self, fount_date: date) -> Record | None:
        query = """select * from api.get_week($1)"""

        week = await self._pool.fetchrow(query, fount_date)
        return week
