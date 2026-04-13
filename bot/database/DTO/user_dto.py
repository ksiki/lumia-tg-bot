from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class UserDTO:
    user_id: int
    name: str
    sex: str
    birthday: date
    birth_time: time
    birth_city: str
    birthday_city_timezone: str
    residence_city: str
    residence_city_timezone: str
    registration_date: date | None
