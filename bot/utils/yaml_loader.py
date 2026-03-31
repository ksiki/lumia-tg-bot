import logging
import yaml
from logging import Logger
from pathlib import Path
from typing import Any, Final


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "assets" / "text_templates"
PROMPTS_PATH: Final[Path] = BASE_DIR / "prompts.yaml"
MESSAGES_PATH: Final[Path] = BASE_DIR / "messages.yaml"
BUTTONS_PATH: Final[Path] = BASE_DIR / "buttons.yaml"

LOG: Final[Logger] = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        LOG.error(f"File not exists: {path}")
        raise FileNotFoundError()

    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            LOG.error(f"Syntax error in YAML file {path}: {e}")
            raise ValueError()
 
    if not isinstance(data, dict):
        if data is None:
            return {}
        LOG.error(f"The {path} file should contain a dictionary (key: value), not {type(data).__name__}")
        raise ValueError()

    return data


PROMPTS: Final[dict[str, Any]] = load_yaml(PROMPTS_PATH)
MESSAGES: Final[dict[str, Any]] = load_yaml(MESSAGES_PATH)
BUTTONS: Final[dict[str, Any]] = load_yaml(BUTTONS_PATH)
