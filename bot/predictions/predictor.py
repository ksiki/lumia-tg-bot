import json
import logging
import random
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Callable, Final
from asyncpg import Record
from openai import AsyncOpenAI

from lexicon.vocabulary import Prompts
from database.data_services import DataServices
from database.DTO import PredictionDTO
from config import DEEPSEEK_API, DEEPSEEK_SECRET


LOG: Final[Logger] = logging.getLogger(__name__) 


class Predictor:
    def __init__(self, data_services: DataServices) -> None:
        self.__data_services = data_services
        self.__client = AsyncOpenAI(
            api_key=DEEPSEEK_SECRET,
            base_url=DEEPSEEK_API
        )

        path = Path(__file__).resolve().parent.parent / "assets/cards_taro/cards_taro_data.json"
        with open(path, "r", encoding="utf-8") as f:
            self.__cards_taro_data = json.load(f)

    async def generate_prediction(self, tg_user_id: int, prod_str_id: str,**kwargs) -> dict[str, Any]:
        LOG.info("Start generate prediction: {prod_str_id}")

        try:   
            user_data = await self.__data_services.get_user_actual_data(tg_user_id)
            prod_data = await self.__data_services.get_product(prod_str_id)

            result = {
                "success": True,
                "uesr_id": tg_user_id,
                "type": prod_str_id,
                "category": prod_data["category"],
                "prediction": None,
                "cards": [],
                "pdf": False
            }

            match prod_str_id:
                case "short_horoscope_for_the_day":
                    result["prediction"] = await self.__generate_short_horoscope_for_the_day(user_data)
                case "one_card_of_the_day":
                    response = await self.__generate_one_card_of_the_day(user_data)
                    result["prediction"] = response[0]
                    result["cards"] = response[1]
                case "full_horoscope_for_the_day":
                    result["prediction"] = await self.__generate_full_horoscope_for_the_day(user_data)
                case "three_tarot_cards_for_the_day":
                    response = await self.__generate_three_tarot_cards_for_the_day(user_data)
                    result["prediction"] = response[0]
                    result["cards"] = response[1]
                case "lunar_horoscope_for_the_week":
                    result["prediction"] = await self.__generate_lunar_horoscope_week(user_data)
                case "one_time_deep_seven_card_hand":
                    response = await self.__generate_one_time_deep_seven_card_hand(user_data, **kwargs)
                    result["prediction"] = response[0]
                    result["cards"] = response[1]
                    result["pdf"] = True
                case "fate_matrix":
                    result["prediction"] = await self.__generate_fate_matrix(tg_user_id, **kwargs)
                    result["pdf"] = True
                case "human_design":
                    result["prediction"] = await self.__generate_human_design(tg_user_id, **kwargs)
                    result["pdf"] = True
                case "deep_compatibility_analysis_synastry":
                    result["prediction"] = await self.__generate_deep_compatibility_analysis_synastry(tg_user_id, **kwargs)
                    result["pdf"] = True
                case "test_of_loyalty":
                    result["prediction"] = await self.__generate_test_of_loyalty(tg_user_id, **kwargs)
                    result["pdf"] = True

            if not result["prediction"]:
                LOG.error("Prediction not generated")
                result["success"] = False
  

            LOG.info(f"End generate prediction: {prod_str_id}")    
            return result
        except Exception as e:
            LOG.error(f"Failed generate prediction: {e}")   
            return {
                "success": False
            }

#===============================================================================================================================================
# services
    async def __get_json_response(self, prompt: str) -> Any:
        response = await self.__client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": Prompts.ROLE.text},
                {"role": "user", "content": prompt}
            ],
            response_format={'type': 'json_object'},
            temperature=0.7
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def __get_random_taro_cards(self, count: int = 1) -> list[list[str]]:
        cards_dict = self.__cards_taro_data.get("cards", {})
        quantity = self.__cards_taro_data.get("quantity", 78)

        numbers = random.sample(range(0, quantity), count)

        cards = []
        for i in numbers:
            card = cards_dict.get(str(i))
            if card:
                cards.append([
                    card.get("file_name")[:-4],
                    card.get("path_to_file"),
                    card.get("tg_cash_id")
                ]) 

        return cards

#===============================================================================================================================================
# tare predictions
    async def __generate_one_card_of_the_day(self, user_data: Record) -> list[Any]:
        cards = self.__get_random_taro_cards()

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
            cards_list=[card[0] for card in cards]
        )
        
        prediction = await self.__get_json_response(prompt)
        return [prediction, cards]
    
    async def __generate_one_time_deep_seven_card_hand(self, user_data: Record, data: str) -> list[Any]:
        cards = self.__get_random_taro_cards(7)

        prompt = Prompts.DEEP_UNDERSTANDING_OF_THE_SITUATION.format(
            user_id=user_data["user_id"],
            situation=data,
            cards_list=[card[0] for card in cards]
        )
        
        prediction = await self.__get_json_response(prompt)
        return [prediction, cards]

#===============================================================================================================================================
# horoscope
    async def __generate_short_horoscope_for_the_day(self, user_data: Record) -> dict[str, str] | None: 
        if not user_data:
            LOG.error("User data is empty")
            return None 

        prompt = Prompts.FREE_HOROSCOPE.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            birth_time=user_data["birth_time"],
            birth_city=user_data["birth_city"],
            current_date=datetime.now().date(),
            sex=user_data["sex"]
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction
    
    async def __generate_full_horoscope_for_the_day(self, user_data: Record) -> dict[str, str] | None: 
        if not user_data:
            LOG.error("User data is empty")
            return None 

        prompt = Prompts.PREMIUM_HOROSCOPE.format(
            user_id=user_data["user_id"],
            name=user_data["name"],
            birthday=user_data["birthday"],
            birth_time=user_data["birth_time"],
            birth_city=user_data["birth_city"],
            current_date=datetime.now().date(),
            sex=user_data["sex"]
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction

    async def __generate_lunar_horoscope_week(self, user_data: Record) -> dict[str, str] | None:
        week = await self.__data_services.get_week(datetime.now().date())
        if not user_data or not week:
            LOG.error("Week or User data is empty")
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
        
        prediction = await self.__get_json_response(prompt)
        return prediction

#===============================================================================================================================================
# microtransactions
    async def __generate_fate_matrix(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.MATRIX_OF_DESTINY.format(
            user_id=user_id,
            user_data=data
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction
    
    async def __generate_human_design(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.HUMAN_DESIGN.format(
            user_id=user_id,
            user_data=data
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction

    async def __generate_deep_compatibility_analysis_synastry(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.COMPATIBILITY_CHART.format(
            user_id=user_id,
            a_b_data=data
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction

    async def __generate_test_of_loyalty(self, user_id: int, data: str) -> dict[str, str]:
        prompt = Prompts.TEST_OF_LOYALTY.format(
            user_id=user_id,
            user_data=data
        )
        
        prediction = await self.__get_json_response(prompt)
        return prediction
