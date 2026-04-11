import re
import httpx
import logging
from datetime import datetime
from timezonefinder import TimezoneFinder
from logging import Logger
from typing import Final
from config import OPENSTREETMAP_API

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


async def is_valid_data_for_prediction(text: str, type: str) -> bool:
    text = text.strip()
    
    date_reg = r"(\d{2}\.\d{2}\.\d{4})"
    time_reg = r"(([01]\d|2[0-3]):[0-5]\d)"
    any_reg = r"(.+)"

    schemas = {
        "fate_matrix": rf"^{date_reg}\n{time_reg}\n{any_reg}$",
        "human_design": rf"^{any_reg}\n{date_reg}\n{time_reg}\n{any_reg}$",
        "deep_compatibility_analysis_synastry": rf"^{any_reg}\n{date_reg}\n{time_reg}\n{any_reg}\n\n{any_reg}\n{date_reg}\n{time_reg}\n{any_reg}$",
        "test_of_loyalty": rf"^{any_reg}\n{date_reg}\n{time_reg}\n{any_reg}\n{any_reg}$",
        "one_time_deep_seven_card_hand": rf"^{any_reg}$"
    }

    match = re.match(schemas.get(type, ""), text)
    if not match:
        LOG.info(f"Regex failed for mode: {type}")
        return False

    groups = match.groups()
    if type == "matrix":
        return is_valid_date(groups[0]) and \
               is_valid_time(groups[1]) and \
               await is_valid_city(groups[3]) is not None
    elif type == "human_design":
        return is_valid_date(groups[1]) and \
               is_valid_time(groups[2]) and \
               await is_valid_city(groups[4]) is not None
    elif type == "compatibility":
        parts = [line.strip() for line in text.split('\n') if line.strip()]
        v1 = is_valid_date(parts[1]) and is_valid_time(parts[2]) and await is_valid_city(parts[3])
        v2 = is_valid_date(parts[5]) and is_valid_time(parts[6]) and await is_valid_city(parts[7])
        return bool(v1 and v2)
    elif type == "deep_understanding":
        return len(text) > 10

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
                OPENSTREETMAP_API, 
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
