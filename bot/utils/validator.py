import re
import httpx
import logging
from datetime import datetime
from timezonefinder import TimezoneFinder
from logging import Logger
from typing import Final


LOG: Final[Logger] = logging.getLogger(__name__)


def is_valid_time(time: str, without_seconds: bool = True) -> bool:
    if not isinstance(time, str):
        LOG.info("Time is not a string.")
        return False

    reg = r"^([01]\d|2[0-3]):[0-5]\d"

    if not without_seconds:
        reg += r":[0-5]\d"

    reg += "$"
    return bool(re.match(reg, time))


def is_valid_date(date: str) -> bool:
    try:
        datetime.strptime(date, "%d.%m.%Y")
        LOG.info("Date is valid")
        return True
    except ValueError:
        LOG.info("Date is not valid")
        return False


TF: Final[TimezoneFinder] = TimezoneFinder()
async def is_valid_city(city: str) -> dict[str, str] | None:
    headers = {"User-Agent": "MyCityValidatorApp/1.0"}
    params = {
        "q": city,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "language": "ru"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search", 
                params=params, 
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            LOG.error(f"Error connecting to Geocoding API: {e}")
            return None

    if not data:
        LOG.info(f"City '{city}' is not valid or not found")
        return None

    result = data[0]
    address = result.get("address", {})
    response_city = address.get("city") or address.get("town") or address.get("village")

    if response_city:
        lat = float(result["lat"])
        lon = float(result["lon"])
        
        timezone = TF.timezone_at(lng=lon, lat=lat)

        LOG.info(f"City '{response_city}' is valid")
        return {
            "city": response_city,
            "timezone": timezone or "Unknown"
        }

    LOG.info(f"Search result for '{city}' is not a city")
    return None
