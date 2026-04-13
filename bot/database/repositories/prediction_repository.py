import json
from asyncpg import Pool, Record

from database.DTO.prediction_dto import PredictionDTO
from database.DTO.get_prediction_dto import GetPredictionDTO
from database.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository):
    def __init__(self, pool: Pool) -> None:
        super().__init__(pool)

    async def add_prediction(self, prediction: PredictionDTO, connection = None) -> int:
        query = "call api.add_prediction($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)"

        conn = connection if connection else self._pool
        prediction_id = await conn.fetchval(
            query,
            prediction.user_id, 
            prediction.prediction_date, 
            prediction.transaction_id,
            prediction.type, 
            prediction.category,
            json.dumps(prediction.prediction, ensure_ascii=False),
            prediction.success,
            prediction.cards,
            prediction.with_pdf,
            None
        )
        return prediction_id

    async def get_prediction(self, found_prediction: GetPredictionDTO) -> Record | None:
        query = "select * from api.get_predictions_by_params($1, $2, $3)"

        prediction = await self._pool.fetchrow(
            query,
            found_prediction.user_id, 
            found_prediction.prediction_date, 
            found_prediction.type
        )
        return prediction
    
    async def get_prediction_by_id(self, prediction_id: int) -> Record | None:
        query = "select * from api.get_prediction_by_id($1)"

        prediction = await self._pool.fetchrow(
            query,
            prediction_id
        )
        return prediction

    async def is_having_prediction(self, found_prediction: GetPredictionDTO) -> bool:
        query = "select * from api.is_having_prediction($1, $2, $3)"

        result = await self._pool.fetchval(
            query,
            found_prediction.user_id, 
            found_prediction.prediction_date, 
            found_prediction.type
        )
        return result
