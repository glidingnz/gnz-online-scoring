"""Configuration loading and validation."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict

import yaml


@dataclass
class SeasonConfig:
    start_date: date
    end_date: date


@dataclass
class AuthConfig:
    username: str = ""
    password: str = ""


@dataclass
class Config:
    season: SeasonConfig
    island_assignment: Dict[int, str] = field(default_factory=dict)
    auth: AuthConfig = field(default_factory=AuthConfig)


def load_config(config_path: Path | str) -> Config:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return parse_config(data)


def parse_config(data: dict) -> Config:
    """Parse and validate configuration data."""
    season_data = data.get("season", {})
    start_str = season_data.get("start_date", "")
    end_str = season_data.get("end_date", "")

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format in config: {e}")

    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    island_assignment: Dict[int, str] = {}
    raw_assignment = data.get("island_assignment") or {}
    for pilot_id, island in raw_assignment.items():
        try:
            pid = int(pilot_id)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid pilot ID: {pilot_id}")
        if island not in ("north", "south"):
            raise ValueError(f"Invalid island '{island}' for pilot {pid}")
        island_assignment[pid] = island

    auth_data = data.get("auth", {})
    auth = AuthConfig(
        username=auth_data.get("username", ""),
        password=auth_data.get("password", ""),
    )

    return Config(
        season=SeasonConfig(start_date=start_date, end_date=end_date),
        island_assignment=island_assignment,
        auth=auth,
    )


def get_default_config_path() -> Path:
    """Get default config path (config.yaml in current directory)."""
    return Path(__file__).parent.parent.parent / "config.yaml"