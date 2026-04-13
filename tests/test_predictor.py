import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from bot.predictions.predictor import Predictor

@pytest.mark.asyncio
class TestPredictor:
    @pytest.fixture
    def mock_data_services(self):
        return AsyncMock()

    @pytest.fixture
    def tarot_data(self):
        return {
            "quantity": 2,
            "cards": {
                "0": {"file_name": "card1.png", "path_to_file": "assets/cards", "tg_cash_id": "id1"},
                "1": {"file_name": "card2.png", "path_to_file": "assets/cards", "tg_cash_id": "id2"}
            }
        }

    @pytest.fixture
    def predictor(self, mock_data_services, tarot_data):
        with patch("builtins.open", mock_open(read_data=json.dumps(tarot_data))):
            return Predictor(mock_data_services)

    async def test_generate_short_horoscope_success(self, predictor, mock_data_services):
        mock_data_services.get_user_actual_data.return_value = {
            "user_id": 1, "name": "Тест", "birthday": "01.01.2000", 
            "birth_time": "12:00", "birth_city": "Минск", "sex": "male"
        }
        mock_data_services.get_product.return_value = {"category": "horoscope"}

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"text": "Вас ждет отличный день!"})
        
        with patch.object(predictor._Predictor__client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await predictor.generate_prediction(1, "short_horoscope_for_the_day")
            
            assert result["success"] is True
            assert result["prediction"]["text"] == "Вас ждет отличный день!"
            assert result["pdf"] is False

    async def test_generate_one_card_of_the_day(self, predictor, mock_data_services):
        mock_data_services.get_user_actual_data.return_value = {
            "user_id": 1, "name": "Тест", "birthday": "01.01.2000"
        }
        mock_data_services.get_product.return_value = {"category": "tarot"}
        
        mock_ai_content = {"interpretation": "Карта сулит успех"}
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(mock_ai_content)

        with patch.object(predictor._Predictor__client.chat.completions, 'create', new_callable=AsyncMock) as mock_create, \
             patch("random.sample", return_value=[0]): 
            mock_create.return_value = mock_response
            
            result = await predictor.generate_prediction(1, "one_card_of_the_day")
            
            assert result["success"] is True
            assert len(result["cards"]) == 1
            assert result["cards"][0][0] == "card1" 
            assert result["prediction"] == mock_ai_content

    async def test_generate_fate_matrix_with_pdf_flag(self, predictor, mock_data_services):
        mock_data_services.get_user_actual_data.return_value = {"user_id": 1}
        mock_data_services.get_product.return_value = {"category": "matrix"}
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"data": "matrix_result"})

        with patch.object(predictor._Predictor__client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await predictor.generate_prediction(1, "fate_matrix", data="22.05.2003")
            
            assert result["success"] is True
            assert result["pdf"] is True

    async def test_prediction_fail_on_exception(self, predictor, mock_data_services):
        mock_data_services.get_user_actual_data.side_effect = Exception("Connection lost")
        
        result = await predictor.generate_prediction(1, "any_type")
        assert result["success"] is False

    def test_get_random_taro_cards_logic(self, predictor):
        """Проверка внутренней логики выбора карт без асинхронности."""
        with patch("random.sample", return_value=[0, 1]):
            cards = predictor._Predictor__get_random_taro_cards(2)
            assert len(cards) == 2
            assert cards[0][0] == "card1"
            assert "assets/cards/card2.png" in cards[1][1]