"""ConfigManager unit tests — saving, loading, recent files, validation."""

import os
import json
import tempfile

import pytest

from config.config_manager import ConfigManager, DEFAULT_CONFIG


@pytest.fixture
def temp_config_path() -> str:
    """Temporary config file path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def config(temp_config_path: str) -> ConfigManager:
    """ConfigManager instance."""
    return ConfigManager(config_path=temp_config_path)


class TestConfigInit:
    """Initialization tests."""

    def test_default_values(self, config: ConfigManager) -> None:
        assert config.get("format") == "png"
        assert config.get("quality") == 90
        assert config.get("theme") == "light"
        assert config.get("undo_limit") == 20

    def test_nonexistent_key(self, config: ConfigManager) -> None:
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"


class TestSaveLoad:
    """Save and load tests."""

    def test_save_and_load(self, temp_config_path: str) -> None:
        config = ConfigManager(config_path=temp_config_path)
        config.set("format", "jpeg")
        config.set("quality", 75)
        config.save()

        # Create new instance — loads from disk
        config2 = ConfigManager(config_path=temp_config_path)
        assert config2.get("format") == "jpeg"
        assert config2.get("quality") == 75

    def test_corrupted_config(self, temp_config_path: str) -> None:
        """A corrupted JSON file should fall back to default values."""
        with open(temp_config_path, "w") as f:
            f.write("{invalid json")

        config = ConfigManager(config_path=temp_config_path)
        assert config.get("format") == "png"

    def test_to_dict(self, config: ConfigManager) -> None:
        result = config.to_dict()
        assert isinstance(result, dict)
        assert "format" in result
        assert "quality" in result


class TestBgColor:
    """Background color tests."""

    def test_default_bg_color(self, config: ConfigManager) -> None:
        color = config.get_bg_color()
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_set_bg_color(self, config: ConfigManager) -> None:
        config.set_bg_color((255, 0, 0))
        assert config.get_bg_color() == (255, 0, 0)


class TestRecentFiles:
    """Recent files tests."""

    def test_empty_recent(self, config: ConfigManager) -> None:
        assert config.get_recent_files() == []

    def test_add_recent(self, config: ConfigManager, temp_config_path: str) -> None:
        config.add_recent_file(temp_config_path)  # Existing file
        recent = config.get_recent_files()
        assert temp_config_path in recent

    def test_recent_dedup(self, config: ConfigManager, temp_config_path: str) -> None:
        """Duplicates should not be added."""
        config.add_recent_file(temp_config_path)
        config.add_recent_file(temp_config_path)
        recent = config.get_recent_files()
        assert recent.count(temp_config_path) == 1

    def test_clear_recent(self, config: ConfigManager, temp_config_path: str) -> None:
        config.add_recent_file(temp_config_path)
        config.clear_recent_files()
        assert config.get_recent_files() == []


class TestValidation:
    """Validation tests."""

    def test_invalid_format(self, temp_config_path: str) -> None:
        with open(temp_config_path, "w") as f:
            json.dump({"format": "invalid_format"}, f)

        config = ConfigManager(config_path=temp_config_path)
        assert config.get("format") == "png"

    def test_invalid_quality(self, temp_config_path: str) -> None:
        with open(temp_config_path, "w") as f:
            json.dump({"quality": 999}, f)

        config = ConfigManager(config_path=temp_config_path)
        assert config.get("quality") == 90

    def test_invalid_theme(self, temp_config_path: str) -> None:
        with open(temp_config_path, "w") as f:
            json.dump({"theme": "neon"}, f)

        config = ConfigManager(config_path=temp_config_path)
        assert config.get("theme") == "light"

    def test_negative_undo_limit(self, temp_config_path: str) -> None:
        with open(temp_config_path, "w") as f:
            json.dump({"undo_limit": -5}, f)

        config = ConfigManager(config_path=temp_config_path)
        assert config.get("undo_limit") == 20
