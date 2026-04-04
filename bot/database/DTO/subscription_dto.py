from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class SubscriptionDTO:
    user_id: int
	transaction_id: int
	start_date: date
	end_date: date
	created_at_time: time
	status: str
