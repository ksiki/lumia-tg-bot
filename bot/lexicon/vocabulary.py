from enum import Enum
from tkinter.messagebox import CANCEL
from lexicon.lexicon_logic import LexiconCore
from utils.yaml_loader import MESSAGES, PROMPTS, BUTTONS


class Msg(LexiconCore, str, Enum):         
    __lexicon_data: dict[str, str] = MESSAGES

    START_MESSAGE = "start_message"
    WHATS_YOUR_NAME_QUESTION = "whats_your_name_question"
    YOUR_GIRL_OR_MAN_QUESTION = "your_girl_or_man_question"
    WHEN_YOUR_BIRTHDAY_QUESTION = "when_your_birthday_question"
    TIME_YOUR_BIRTH_QUESTION = "time_your_birth_question"
    YOUR_CITY_BIRTH_QUESTION = "your_city_birth_question"
    YOUR_CITY_RESIDENCE_QUESTION = "your_city_residence_question"
    SUCCESSFUL_REGISTRATION = "successful_acquaintance"
    PREMIUM_GIFT_THREE_DAYS = "premium_gift_five_days"

    NOT_VALID_YOUR_CITY_QUESTION = "not_valid_your_city_question"
    NOT_VALID_TIME_YOUR_BIRTH_QUESTION = "not_valid_time_your_birth_question"
    NOT_VALID_WHEN_YOUR_BIRTHDAY_QUESTION = "not_valid_when_your_birthday_question"

    MENU_MESSAGE = "menu_message"
    FAILED_ANSWER_INVOICE = "failed_answer_invoice"
    FAILED_PREDICTION_REFUND = "failed_prediction_refund"
    SECCESSFUL_SUBSCRIPTION_PURCHASE = "successful_subscription_purchase"

    REQUEST_DATA_FOR_DEEP_UNDERSTANDING = "request_data_for_deep_understanding"
    REQUEST_DATA_MATRIX_OF_DESTINY = "request_data_matrix_of_destiny"
    REQUEST_DATA_HUMAN_DESIGN = "request_data_human_design"
    REQUEST_DATA_COMPATIBILITY_CHART = "request_data_compatibility_chart"
    REQUEST_DATA_TEST_OF_LOYALTY = "request_data_test_of_loyalty"
    FAILED_DATA_FOR_PREDICTION = "failed_data_for_prediction"
    WAITING_FOR_PREDICTION = "waiting_for_prediction"


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
    PAY = "pay"
    CANCEL = "cancel"
    OPEN_MENU = "open_menu"


class Prompts(LexiconCore, str, Enum):
    __lexicon_data: dict[str, str] = PROMPTS

    ROLE = "role"
    LUNAR_HOROSCOPE_ON_THE_WEEK = "lunar_horoscope_on_the_week"
    TARO_ONE_CARD = "taro_one_card"
    TARO_THREE_CARDS = "taro_three_cards"
    DEEP_UNDERSTANDING_OF_THE_SITUATION = "deep_understanding_of_the_situation"
    MATRIX_OF_DESTINY = "matrix_of_destiny"
    HUMAN_DESIGN = "human_design"
    COMPATIBILITY_CHART = "compatibility_chart"
    TEST_OF_LOYALTY = "test_of_loyalty" 
    FREE_HOROSCOPE = "free_horoscope"
    PREMIUM_HOROSCOPE = "premium_horoscope"
    