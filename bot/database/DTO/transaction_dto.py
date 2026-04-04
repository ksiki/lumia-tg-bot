from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class TransactionDTO:
    user_id: int
    product_str_id: str
    date_transaction: date
    time_transaction: time
    stars_price_original: int
    stars_price_actual: int
    token: str
    is_subscription_active: bool
