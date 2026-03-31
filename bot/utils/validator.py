import re
import logging
from datetime import datetime
from dadata import DadataAsync
from httpx import HTTPStatusError
from logging import Logger
from typing import Final

from config import DADATA_API, DADATA_SECRET


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


async def is_valid_city(city: str) -> dict[str, str] | None:
    async with DadataAsync(DADATA_API, DADATA_SECRET) as data:  # pyright: ignore[reportGeneralTypeIssues]
        try:
            response: dict = await data.clean("address", city)
        except HTTPStatusError:
            LOG.error("HTTPStatusError")
            return None

        response_city = response.get("city")
        if response_city:
            LOG.info("City is valid")
            return {
                "city": response_city,
                "country": response.get("country"),
                "iso_code": response.get("country_iso_code"),
                "timezone": response.get("timezone")
            }  # pyright: ignore[reportReturnType]
    
    LOG.info("City is not valid")
    return None
