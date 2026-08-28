import os
import tomllib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


DEFAULT_PATH = Path.home().joinpath(".config/grisha.toml")


@dataclass
class Creds:
    cc_token: str
    telegram_token: str


@dataclass
class Settings:
    db_path: str = str(Path.home().joinpath(".local/share/grisha.db"))


@dataclass
class Config:
    creds: Creds
    settings: Settings


def _load() -> Config:
    if "CONFIG_PATH" in os.environ:
        path = Path(os.environ["CONFIG_PATH"])
    else:
        path = DEFAULT_PATH

    toml_config: dict[str, Any] = {}
    with path.open("br") as f:
        toml_config = tomllib.load(f)
        if "Creds" not in toml_config:
            raise ValueError("'Creds' section is required in config")

    return Config(
        creds=Creds(**toml_config.get("Creds", {})),
        settings=Settings(**toml_config.get("Settings", {})),
    )


CONFIG = _load()
logger.debug(f"Loaded config:\n{CONFIG}")
