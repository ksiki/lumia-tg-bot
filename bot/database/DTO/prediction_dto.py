from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class PredictionDTO:
    user_id: int
    prediction_date: date
    type: str
    prediction: dict[str, Any]
