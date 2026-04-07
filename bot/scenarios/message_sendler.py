from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext

from scenarios.fsm_states import States


async def send_message(message: Message, mes_text: str, state: FSMContext = None, newState: States = None, reply_markup: ReplyKeyboardMarkup = None) -> Message:
    response = await message.answer(mes_text,
                                    reply_markup=reply_markup)

    if state and newState:
        await state.set_state(newState)

    return response
