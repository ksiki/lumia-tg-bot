from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class ActionLogDTO:
    user_id: int
    message_text: str
	response: str
	date_log: date 
	time_log: time
