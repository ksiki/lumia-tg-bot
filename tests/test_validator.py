import pytest
from unittest.mock import AsyncMock, patch
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
    @patch("bot.utils.validator.DadataAsync")
    async def test_is_valid_city_success(self, mock_class):
        mock = AsyncMock()
        mock.clean.return_value = {
            "city": "Минск",
            "country": "Беларусь",
            "iso_code": "BY",
            "timezone": "UTC+3"
        }

        mock_class.return_value.__aenter__.return_value = mock

        result = await is_valid_city("Минск")

        assert result["city"] == "Минск"
        assert result["country"] == "Беларусь"
        assert result["iso_code"] == "BY"
        assert result["timezone"] == "UTC+3"
        mock.clean.assert_called_once_with("address", "Минск")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "city, result",
        [
            (None, None),
            (123, None),
        ]
    )
    async def test_is_valid_city_invalid_input(self, city, result):
        assert await is_valid_city(city) is result
