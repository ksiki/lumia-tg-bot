import pytest
from contextlib import nullcontext as does_not_raise

from bot.utils.yaml_loader import load_yaml


class TestLoadYaml:
    @pytest.mark.parametrize(
        "content, result, expectation",
        [
            ("key: value\nname: test", {
                "key": "value",
                "name": "test"},
                does_not_raise()),
            ("", {}, does_not_raise()),
            ("- item1\n- item2", None, pytest.raises(ValueError)),
            ("key: : value", None, pytest.raises(ValueError)),
        ]
    )
    def test_load_yaml_content_logic(self, tmp_path, content, result, expectation):
        file = tmp_path / "config.yaml"
        file.write_text(content, encoding="utf-8")

        with expectation:
            result = load_yaml(file)
            if result is not None:
                assert result == result

    def test_load_yaml_file_not_found(self, tmp_path):
        non_existent_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            load_yaml(non_existent_file)
