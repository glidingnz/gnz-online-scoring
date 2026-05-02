"""Tests for configuration loading."""

import pytest
from datetime import date
from pathlib import Path
import tempfile

from src.weglide_client.config import load_config, parse_config


class TestParseConfig:
    def test_valid_config(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
            "island_assignment": {},
        }
        config = parse_config(data)
        assert config.season.start_date == date(2024, 10, 1)
        assert config.season.end_date == date(2025, 3, 31)

    def test_island_assignment_parsed(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
            "island_assignment": {
                "123": "north",
                "456": "south",
            },
        }
        config = parse_config(data)
        assert config.island_assignment == {123: "north", 456: "south"}

    def test_invalid_start_date_before_end_date(self):
        data = {
            "season": {
                "start_date": "2025-10-01",
                "end_date": "2024-03-31",
            },
        }
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            parse_config(data)

    def test_invalid_date_format(self):
        data = {
            "season": {
                "start_date": "invalid",
                "end_date": "2025-03-31",
            },
        }
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_config(data)

    def test_invalid_island_value(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
            "island_assignment": {"123": "invalid"},
        }
        with pytest.raises(ValueError, match="Invalid island"):
            parse_config(data)

    def test_invalid_pilot_id(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
            "island_assignment": {"abc": "north"},
        }
        with pytest.raises(ValueError, match="Invalid pilot ID"):
            parse_config(data)

    def test_auth_config_parsed(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
            "auth": {
                "username": "testuser",
                "password": "testpass",
            },
        }
        config = parse_config(data)
        assert config.auth.username == "testuser"
        assert config.auth.password == "testpass"

    def test_auth_config_empty(self):
        data = {
            "season": {
                "start_date": "2024-10-01",
                "end_date": "2025-03-31",
            },
        }
        config = parse_config(data)
        assert config.auth.username == ""
        assert config.auth.password == ""


class TestLoadConfig:
    def test_load_from_file(self):
        tmpdir = tempfile.mkdtemp()
        filepath = Path(tmpdir) / "config.yaml"
        filepath.write_text("season:\n  start_date: '2024-10-01'\n  end_date: '2025-03-31'\n")
        try:
            config = load_config(filepath)
            assert config.season.start_date == date(2024, 10, 1)
        finally:
            filepath.unlink()
            Path(tmpdir).rmdir()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")