import logging
import yaml
from logging import Logger
from pathlib import Path
from typing import Any, Final


TEMPLATES_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "assets" / "text_templates"
PROMPTS_PATH: Final[Path] = TEMPLATES_DIR / "prompts.yaml"
MESSAGES_PATH: Final[Path] = TEMPLATES_DIR / "messages.yaml"
BUTTONS_PATH: Final[Path] = TEMPLATES_DIR / "buttons.yaml"

LOG: Final[Logger] = logging.getLogger(__name__)


def load_yaml(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        LOG.error(f"File missing: {file_path}")
        raise FileNotFoundError(f"Missing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        LOG.error(f"YAML syntax error in {file_path.name}: {e}")
        raise ValueError(f"Invalid YAML: {file_path}")

    if data is None:
        LOG.info(f"File {file_path.name} is empty")
        return {}

    if not isinstance(data, dict):
        LOG.error(f"Format error in {file_path.name}: expected dict, got {type(data).__name__}")
        raise ValueError(f"YAML in {file_path} must be a dictionary")

    LOG.info(f"Loaded {file_path.name}")
    return data


PROMPTS: Final[dict[str, Any]] = load_yaml(PROMPTS_PATH)
MESSAGES: Final[dict[str, Any]] = load_yaml(MESSAGES_PATH)
BUTTONS: Final[dict[str, Any]] = load_yaml(BUTTONS_PATH)