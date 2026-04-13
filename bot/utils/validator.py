import re
import httpx
import logging
from datetime import datetime
from timezonefinder import TimezoneFinder
from logging import Logger
from typing import Final
from config import OPENSTREETMAP_API

LOG: Final[Logger] = logging.getLogger(__name__)

DATE_FORMAT: str = "%d.%m.%Y"
TIME_PATTERN_BASE: Final[str] = r"^([01]\d|2[0-3]):[0-5]\d"
TIME_PATTERN_SECONDS: Final[str] = r":[0-5]\d"

GEO_USER_AGENT: Final[dict[str, str]] = {"User-Agent": "MyCityValidatorApp/1.0"}
GEO_TIMEOUT: Final[float] = 10.0
MIN_LOYALTY_VAL_LEN: Final[int] = 3
MIN_CARD_HAND_LEN: Final[int] = 50

MODE_FATE_MATRIX: Final[str] = "fate_matrix"
MODE_HUMAN_DESIGN: Final[str] = "human_design"
MODE_SYNASTRY: Final[str] = "deep_compatibility_analysis_synastry"
MODE_LOYALTY: Final[str] = "test_of_loyalty"
MODE_CARD_HAND: Final[str] = "one_time_deep_seven_card_hand"


def is_valid_time(time_str: str, without_seconds: bool = True) -> bool:
    if not isinstance(time_str, str):
        LOG.info("Time validation failed: input is not a string")
        return False

    pattern = TIME_PATTERN_BASE
    if not without_seconds:
        pattern += TIME_PATTERN_SECONDS

    pattern += "$"
    return bool(re.match(pattern, time_str))


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        LOG.info(f"Date '{date_str}' is valid")
        return True
    except ValueError:
        LOG.info(f"Date '{date_str}' has invalid format")
        return False


async def is_valid_data_for_prediction(text: str, prediction_type: str) -> bool:
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

    pattern = schemas.get(prediction_type)
    if not pattern:
        LOG.error(f"Unknown prediction type: {prediction_type}")
        return False

    match = re.match(pattern, text)
    if not match:
        LOG.info(f"Regex mismatch for mode: {prediction_type}")
        return False

    groups = match.groups()

    if prediction_type == MODE_FATE_MATRIX:
        is_date_ok = is_valid_date(groups[0])
        is_time_ok = is_valid_time(groups[1])
        city_data = await is_valid_city(groups[3])
        return is_date_ok and is_time_ok and city_data is not None
    elif prediction_type == MODE_HUMAN_DESIGN:
        return is_valid_date(groups[1]) and is_valid_time(groups[2])
    elif prediction_type == MODE_LOYALTY:
        return is_valid_date(groups[1]) and is_valid_time(groups[2]) and len(groups[5]) >= MIN_LOYALTY_VAL_LEN
    elif prediction_type == MODE_SYNASTRY:
        parts = [line.strip() for line in text.split('\n') if line.strip()]
        if len(parts) < 8:
            return False
        first_person_valid = is_valid_date(parts[1]) and is_valid_time(parts[2])
        second_person_valid = is_valid_date(parts[5]) and is_valid_time(parts[6])
        return bool(first_person_valid and second_person_valid)
    elif prediction_type == MODE_CARD_HAND:
        return len(text) > MIN_CARD_HAND_LEN

    return False


TF: Final[TimezoneFinder] = TimezoneFinder()
async def is_valid_city(city: str) -> dict[str, str] | None:
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
                headers=GEO_USER_AGENT,
                timeout=GEO_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            LOG.error(f"Geocoding API connection error: {e}")
            return None

    result = data[0]
    address = result.get("address", {})
    response_city = (
        address.get("city") or 
        address.get("town") or 
        address.get("village") or 
        address.get("hamlet") or
        address.get("state") or       
        address.get("municipality") or
        address.get("county")
    )

    if response_city:
        lat = float(result["lat"])
        lon = float(result["lon"])
        timezone = TF.timezone_at(lng=lon, lat=lat)

        LOG.info(f"City '{response_city}' validated successfully")
        return {
            "city": response_city,
            "timezone": timezone or "Unknown"
        }

    LOG.info(f"Geocoding result for '{city}' is not a valid city type")
    return None