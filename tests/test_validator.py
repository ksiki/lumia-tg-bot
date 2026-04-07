import pytest
import respx
from httpx import Response
from unittest.mock import patch
from contextlib import nullcontext as does_not_raise

from bot.utils.validator import is_valid_city, is_valid_date, is_valid_time


class TestValidator:
    @pytest.mark.parametrize(
        "date, result, expectation",
        [
            ("22.05.2003", True, does_not_raise()),
            ("35.05.2003", False, does_not_raise()),
            ("29.02.2024", True, does_not_raise()),
            ("29.02.2023", False, does_not_raise()),
            ("4kglf", False, does_not_raise()),
            (None, False, pytest.raises(TypeError)),
        ]
    )
    def test_is_valid_date(self, date, result, expectation):
        with expectation:
            assert is_valid_date(date) is result

    @pytest.mark.parametrize(
        "time, result",
        [
            ("15:30", True),
            ("00:00", True),
            ("23:59", True),
            ("26:30", False),
            ("15:60", False),
            (1500, False),
            (None, False),
        ]
    )
    def test_is_valid_time(self, time, result):
        assert is_valid_time(time) is result

    @pytest.mark.asyncio
    async def test_is_valid_city_success(self):
        city_name = "Минск"
        mock_data = [{
            "lat": "53.9022",
            "lon": "27.5618",
            "address": {"city": "Минск"}
        }]

        with respx.mock:
            respx.get("https://nominatim.openstreetmap.org/search").mock(
                return_value=Response(200, json=mock_data)
            )
            
            with patch("bot.utils.validator.TF") as mock_tf:
                mock_tf.timezone_at.return_value = "Europe/Minsk"
                
                result = await is_valid_city(city_name)
                
                assert result is not None
                assert result["city"] == "Минск"
                assert result["timezone"] == "Europe/Minsk"

    @pytest.mark.asyncio
    async def test_is_valid_city_not_found(self):
        with respx.mock:
            respx.get("https://nominatim.openstreetmap.org/search").mock(
                return_value=Response(200, json=[])
            )
            
            result = await is_valid_city("НесуществующийГород")
            assert result is None

    @pytest.mark.asyncio
    async def test_is_valid_city_api_error(self):
        with respx.mock:
            respx.get("https://nominatim.openstreetmap.org/search").mock(
                return_value=Response(500)
            )
            
            result = await is_valid_city("Минск")
            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "city_input",
        [None, 123, ""]
    )
    async def test_is_valid_city_invalid_input(self, city_input):
        with respx.mock:
            respx.get("https://nominatim.openstreetmap.org/search").mock(
                return_value=Response(200, json=[])
            )
            result = await is_valid_city(city_input)
            assert result is None
