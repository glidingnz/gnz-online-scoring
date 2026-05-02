"""Configuration classes."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict


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