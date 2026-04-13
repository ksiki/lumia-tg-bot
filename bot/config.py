from decouple import config
from typing import Final


TOKEN: Final[str] = config("TOKEN")
PG_LINK: Final[str] = config("PG_LINK")
REDIS_LINK: Final[str] = config("REDIS_LINK")
DEBUG: Final[bool] = config("DEBUG", default=False, cast=bool)
ADMINS: Final[list[int]] = [int(admin_id) for admin_id in config("ADMINS").split(",")]
DIRRECT_LINK: Final[str] = config("DIRRECT_LINK")
STARS_SHOP_LINK: Final[str] = config("STARS_SHOP_LINK")

DEEPSEEK_API = "https://api.deepseek.com"
DEEPSEEK_SECRET = config("DEEPSEEK_SECRET")

OPENSTREETMAP_API = "https://nominatim.openstreetmap.org/search"