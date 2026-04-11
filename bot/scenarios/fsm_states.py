from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    START_REGISTRATION = State()
    WHATS_YOUR_NAME = State()
    YOUR_GIRL_OR_MAN = State()
    WHEN_YOUR_BIRTHDAY = State()
    TIME_YOUR_BIRTH = State()
    YOUR_CITY_BIRTH = State()
    YOUR_CITY_RESIDENCE = State()
    SUCCESSFUL_ACQUAINTANCE = State()
    PREMIUM_GIFT_THREE_DAYS = State()

    MENU = State()
    CONFIRM_PAYMENT = State()
    REQUEST_DATA = State
    SAVE_REQUEST_DATA = State()
    WAITING_PREDICTION = State()