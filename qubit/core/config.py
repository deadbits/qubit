"""Configuration handler."""

from typing import Optional
from pathlib import Path
import yaml

from qubit.models.config import Config


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file."""
    if not config_path:
        config_path = "data/config.yaml"

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)


config: Config = None
