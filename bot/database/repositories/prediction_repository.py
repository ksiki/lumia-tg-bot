from asyncpg import Pool, Record

from database.DTO.prediction_dto import PredictionDTO
from database.DTO.get_prediction_dto import GetPredictionDTO
from database.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def add_prediction(self, prediction: PredictionDTO) -> None:
        query = "call api.add_prediction($1, $2, $3, $4)"

        await self._pool.execute(
            query,
            prediction.user_id, 
            prediction.prediction_date, 
            prediction.type, 
            prediction.prediction
        )

    async def get_prediction(self, found_prediction: GetPredictionDTO) -> Record | None:
        query = """
            select *
            from mart.v_prediction vp
            where user_id = $1
                and date = $2
                and type = $3 
        """

        prediction = await self._pool.fetchrow(
            query,
            found_prediction.user_id, 
            found_prediction.prediction_date, 
            found_prediction.type
        )
        return prediction