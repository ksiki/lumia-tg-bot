from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class PredictionDTO:
    user_id: int
    prediction_date: date
    p_transaction_id: int | None
    type: str
    category: str
    prediction: dict[str, Any]
    success: bool
    cards: str
    with_pdf: bool
