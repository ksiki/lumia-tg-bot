from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class GetPredictionDTO:
    user_id: int
    prediction_date: date
    type: str