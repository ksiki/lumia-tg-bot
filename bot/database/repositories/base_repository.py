from asyncpg import Pool


class BaseRepository:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool
