from asyncpg import Pool

from database.DTO.action_log_dto import ActionLogDTO
from database.repositories.base_repository import BaseRepository


class ActionLogRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def add_action_log(self, action_log: ActionLogDTO) -> None:
        query = "call api.add_action_log($1, $2, $3, $4, $5)"

        await self._pool.execute(
            query,
            action_log.user_id, 
            action_log.message_text, 
            action_log.response, 
            action_log.date_log,
            action_log.time_log
        )
