from enum import Enum
from lexicon.lexicon_logic import LexiconCore
from utils.yaml_loader import MESSAGES, PROMPTS, BUTTONS


class Msg(LexiconCore, str, Enum):         
    __lexicon_data: dict[str, str] = MESSAGES

    MENU_MESSAGE = "menu_message"

    # start dialogue
    START_MESSAGE = "start_message"
    WHATS_YOUR_NAME_QUESTION = "whats_your_name_question"
    YOUR_GIRL_OR_MAN_QUESTION = "your_girl_or_man_question"
    WHEN_YOUR_BIRTHDAY_QUESTION = "when_your_birthday_question"
    TIME_YOUR_BIRTH_QUESTION = "time_your_birth_question"
    YOUR_CITY_BIRTH_QUESTION = "your_city_birth_question"
    YOUR_CITY_RESIDENCE_QUESTION = "your_city_residence_question"
    SUCCESSFUL_REGISTRATION = "successful_acquaintance"
    PREMIUM_GIFT_FIVE_DAYS = "premium_gift_five_days"

    NOT_VALID_YOUR_CITY_QUESTION = "not_valid_your_city_question"
    NOT_VALID_TIME_YOUR_BIRTH_QUESTION = "not_valid_time_your_birth_question"
    NOT_VALID_WHEN_YOUR_BIRTHDAY_QUESTION = "not_valid_when_your_birthday_question"


class Buttons(LexiconCore, str, Enum):
    __lexicon_data: dict[str, str] = BUTTONS

    START_ACQUAINTANCE = "start_acquaintance"
    GIRL = "girl"
    MAN = "man"
    FORTH = "forth"
    ACTIVATE = "activate"
    AGAIN = "again"
    PRODUCT_BATTON_WITH_PRICE = "product_batton_with_price"
    PRODUCT_BATTON_WITHOUT_PRICE = "product_batton_without_price"


class Prompts(LexiconCore, str, Enum):
    __lexicon_data: dict[str, str] = PROMPTS
