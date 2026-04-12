import logging
from logging import Logger
from typing import Final
from datetime import datetime, date, time

LOG: Final[Logger] = logging.getLogger(__name__)
DATE_PARSE_FORMAT: Final[str] = "%d.%m.%Y"
TIME_PARSE_FORMAT: Final[str] = "%H:%M"


def str_to_date(date_str: str) -> date:
    date_obj = datetime.now().date()
    try:
        date_obj = datetime.strptime(date_str, DATE_PARSE_FORMAT).date()
        LOG.inf(f"Successfully converted string to date: {date_str}")
    except Exception as e:
        LOG.error(f"Error in {__name__} while parsing date: {e}")

    return date_obj


def str_to_time(time_str: str) -> time:
    time_obj = datetime.now().time()
    try:
        time_obj = datetime.strptime(time_str, TIME_PARSE_FORMAT).time()
        LOG.inf(f"Successfully converted string to time: {time_str}")
    except Exception as e:
        LOG.error(f"Error in {__name__} while parsing time: {e}")

    return time_obj