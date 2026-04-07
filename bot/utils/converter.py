import logging
from logging import Logger
from typing import Final
from datetime import datetime, date, time


LOG: Final[Logger] = logging.getLogger(__name__)


def str_to_date(date_str: str) -> date:
    date_obj = datetime.now().date()
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
    except Exception as e:
        LOG.error(f"Error in {__name__}: {e}")

    return date_obj


def str_to_time(time_str: str) -> time:
    time_obj = datetime.now().time()
    try:
        time_obj = datetime.strptime(time_str, "%H:%M").time()
    except Exception as e:
        LOG.error(f"Error in {__name__}: {e}")

    return time_obj