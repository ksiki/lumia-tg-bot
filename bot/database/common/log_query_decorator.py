import logging
import functools
import time
from logging import Logger
from typing import Any, Final, Collable


LOG: Final[Logger] = logging.getLogger(__name__)


def log_query(logger: Logger = LOG):
    def decorator(func: Collable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = 0
            
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"DB Request: {func.__qualname__}; Arguments: {args} | {kwargs}")
                start_time = time.perf_counter()
            
            try:
                response = await func(*args, **kwargs)

                if logger.isEnabledFor(logging.INFO):
                    duration = time.perf_counter() - start_time
                    str_res = str(response)[:200]
                    logger.info(f"Success {func.__qualname__} in {duration:.4f}s | Res: {str_res}...")
    
                return response
            except Exception as e:
                logger.error(f"Error in {func.__qualname__}: {e}")
                raise
        return wrapper
    return decorator
