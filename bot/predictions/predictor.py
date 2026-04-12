import json
import logging
import random
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Final

from asyncpg import Record
from openai import AsyncOpenAI

from lexicon.vocabulary import Prompts
from database.data_services import DataServices
from config import DEEPSEEK_API, DEEPSEEK_SECRET

LOG: Final[Logger] = logging.getLogger(__name__)
TAROT_DATA_PATH: Final[str] = "assets/cards_taro/cards_taro_data.json"
AI_MODEL: Final[str] = "deepseek-chat"
AI_TEMPERATURE: Final[float] = 0.7
DEFAULT_TAROT_QUANTITY: Final[int] = 78


class Predictor:
    def __init__(self, data_services: DataServices) -> None:
        self.__data_services = data_services
        self.__client = AsyncOpenAI(
            api_key=DEEPSEEK_SECRET,
            base_url=DEEPSEEK_API
        )

        self.__base_dir = Path(__file__).resolve().parent.parent
        data_file = self.__base_dir / TAROT_DATA_PATH
        with open(data_file, "r", encoding="utf-8") as f:
            self.__cards_taro_data = json.load(f)

    async def generate_prediction(self, tg_user_id: int, prod_str_id: str, **kwargs) -> dict[str, Any]:
        LOG.info(f"Start prediction generation: {prod_str_id} for user {tg_user_id}")

        try:
            user_data = await self.__data_services.get_user_actual_data(tg_user_id)
            prod_data = await self.__data_services.get_product(prod_str_id)

            result = {
                "success": True,
                "user_id": tg_user_id,
                "type": prod_str_id,
                "category": prod_data["category"],
                "prediction": None,
                "cards": [],
                "pdf": False
            }

            if prod_str_id == "short_horoscope_for_the_day":
                result["prediction"] = await self.__generate_short_horoscope_for_the_day(user_data)
            elif prod_str_id == "full_horoscope_for_the_day":
                result["prediction"] = await self.__generate_full_horoscope_for_the_day(user_data)
            elif prod_str_id == "lunar_horoscope_for_the_week":
                result["prediction"] = await self.__generate_lunar_horoscope_week(user_data)
            elif prod_str_id == "one_card_of_the_day":
                pred, cards = await self.__generate_one_card_of_the_day(user_data)
                result.update({"prediction": pred, "cards": cards})
            elif prod_str_id == "three_tarot_cards_for_the_day":
                pred, cards = await self.__generate_three_tarot_cards_for_the_day(user_data)
                result.update({"prediction": pred, "cards": cards})
            elif prod_str_id == "one_time_deep_seven_card_hand":
                pred, cards = await self.__generate_one_time_deep_seven_card_hand(user_data, **kwargs)
                result.update({"prediction": pred, "cards": cards, "pdf": True})
            elif prod_str_id == "fate_matrix":
                result["prediction"] = await self.__generate_fate_matrix(tg_user_id, **kwargs)
                result["pdf"] = True
            elif prod_str_id == "human_design":
                result["prediction"] = await self.__generate_human_design(tg_user_id, **kwargs)
                result["pdf"] = True
            elif prod_str_id == "deep_compatibility_analysis_synastry":
                result["prediction"] = await self.__generate_deep_compatibility_analysis_synastry(tg_user_id, **kwargs)
                result["pdf"] = True
            elif prod_str_id == "test_of_loyalty":
                result["prediction"] = await self.__generate_test_of_loyalty(tg_user_id, **kwargs)
                result["pdf"] = True
            if not result["prediction"]:
                LOG.error(f"Prediction result is empty for {prod_str_id}")
                return {"success": False}

            LOG.info(f"Successfully generated: {prod_str_id}")
            return result

        except Exception as e:
            LOG.error(f"Prediction generation failed: {e}")
            return {"success": False}

# ======================================================================================================================
# services
    async def __get_json_response(self, prompt: str) -> Any:
        response = await self.__client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": Prompts.ROLE.text},
                {"role": "user", "content": prompt}
            ],
            response_format={'type': 'json_object'},
            temperature=AI_TEMPERATURE
        )
        return json.loads(response.choices[0].message.content)

    def __get_random_taro_cards(self, count: int = 1) -> list[list[str]]:
        cards_dict = self.__cards_taro_data.get("cards", {})
        total_quantity = self.__cards_taro_data.get("quantity", DEFAULT_TAROT_QUANTITY)

        indices = random.sample(range(total_quantity), count)
        selected_cards = []

        for idx in indices:
            card = cards_dict.get(str(idx))
            if card:
                name = card.get("file_name", "")[:-4]
                full_path = str(self.__base_dir / card.get("path_to_file") / card.get("file_name"))
                selected_cards.append([name, full_path, card.get("tg_cash_id")])

        return selected_cards

# ======================================================================================================================
# tarot predictions
    async def __generate_one_card_of_the_day(self, user_data: Record) -> list[Any]:
        cards = self.__get_random_taro_cards(1)
        prompt = Prompts.TARO_ONE_CARD.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            current_date=datetime.now().date(),
            card_name=cards[0][0]
        )
        prediction = await self.__get_json_response(prompt)
        return [prediction, cards]

    async def __generate_three_tarot_cards_for_the_day(self, user_data: Record) -> list[Any]:
        cards = self.__get_random_taro_cards(3)
        prompt = Prompts.TARO_THREE_CARDS.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            current_date=datetime.now().date(),
            cards_list=",".join(c[0] for c in cards)
        )
        prediction = await self.__get_json_response(prompt)
        return [prediction, cards]

    async def __generate_one_time_deep_seven_card_hand(self, user_data: Record, data: str) -> list[Any]:
        cards = self.__get_random_taro_cards(7)
        prompt = Prompts.DEEP_UNDERSTANDING_OF_THE_SITUATION.format(
            user_id=user_data["user_id"],
            situation=data,
            cards_list=",".join(c[0] for c in cards)
        )
        prediction = await self.__get_json_response(prompt)
        return [prediction, cards]

# ======================================================================================================================
# horoscope
    async def __generate_short_horoscope_for_the_day(self, user_data: Record) -> dict[str, str] | None:
        prompt = Prompts.FREE_HOROSCOPE.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            birth_time=user_data["birth_time"],
            birth_city=user_data["birth_city"],
            current_date=datetime.now().date(),
            sex=user_data["sex"]
        )
        return await self.__get_json_response(prompt)

    async def __generate_full_horoscope_for_the_day(self, user_data: Record) -> dict[str, str] | None:
        prompt = Prompts.PREMIUM_HOROSCOPE.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            birth_time=user_data["birth_time"],
            birth_city=user_data["birth_city"],
            current_date=datetime.now().date(),
            sex=user_data["sex"]
        )
        return await self.__get_json_response(prompt)

    async def __generate_lunar_horoscope_week(self, user_data: Record) -> dict[str, str] | None:
        week = await self.__data_services.get_week(datetime.now().date())
        if not week:
            LOG.error("Week data not found in DB")
            return None

        prompt = Prompts.LUNAR_HOROSCOPE_ON_THE_WEEK.format(
            start_date=week["start_date"],
            end_date=week["end_date"],
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            birth_time=user_data["birth_time"],
            birth_place=user_data["birth_city"],
            residence_place=user_data["residence_city"],
            sex=user_data["sex"]
        )
        return await self.__get_json_response(prompt)

# ======================================================================================================================
# microtransactions
    async def __generate_fate_matrix(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.MATRIX_OF_DESTINY.format(user_id=user_id, user_data=data)
        return await self.__get_json_response(prompt)

    async def __generate_human_design(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.HUMAN_DESIGN.format(user_id=user_id, user_data=data)
        return await self.__get_json_response(prompt)

    async def __generate_deep_compatibility_analysis_synastry(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.COMPATIBILITY_CHART.format(user_id=user_id, a_b_data=data)
        return await self.__get_json_response(prompt)

    async def __generate_test_of_loyalty(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.TEST_OF_LOYALTY.format(user_id=user_id, user_data=data)
        return await self.__get_json_response(prompt)