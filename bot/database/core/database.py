import asyncpg
import logging
from logging import Logger
from asyncpg import Pool
from typing import Final


LOG: Final[Logger] = logging.getLogger(__name__)


class Database:
    def __init__(self, link: str) -> None:
        self.__link: Final[str] = link
        self.__pool: Final[Pool] = None

    @property
    def pool(self) -> Pool:
        return self.__pool

    async def connect(self) -> None:
        if not self.__pool:
            try:
                self.__pool = await asyncpg.create_pool(dsn=self.__link)
                LOG.info("Connection pool created")
            except Exception as e:
                LOG.error(f"Failed to create pool: {e}")
                raise

    async def disconnect(self) -> None:
        if self.__pool:
            await self.__pool.close()
            LOG.info("Connection pool closed")
        else:
            LOG.info("Connection pool is not exists")
