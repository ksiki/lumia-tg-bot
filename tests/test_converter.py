import pytest
from datetime import date, time, datetime
from unittest.mock import patch
from bot.utils.converter import str_to_date, str_to_time

class TestConverter:
    def test_str_to_date_success(self):
        input_str = "22.05.2003"
        expected = date(2003, 5, 22)
        assert str_to_date(input_str) == expected

    def test_str_to_date_fallback(self):
        fixed_now = datetime(2026, 4, 13, 10, 0, 0)
        with patch("bot.utils.converter.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.strptime.side_effect = ValueError("Invalid format")
            result = str_to_date("invalid-date-string")
            assert result == fixed_now.date()


    def test_str_to_time_success(self):
        input_str = "15:30"
        expected = time(15, 30)
        assert str_to_time(input_str) == expected

    def test_str_to_time_fallback(self):
        fixed_now = datetime(2026, 4, 13, 15, 45, 0)
        with patch("bot.utils.converter.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.strptime.side_effect = ValueError("Invalid format")
            result = str_to_time("99:99")
            assert result == fixed_now.time()

    @pytest.mark.parametrize("invalid_input", [None, "", "31-12-2022", "wrong"])
    def test_str_to_date_robustness(self, invalid_input):
        result = str_to_date(invalid_input)
        assert isinstance(result, date)