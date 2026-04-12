from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from keepassxc_cli.config import CliConfig, DEFAULT_BROWSER_API_CONFIG_PATH, DEFAULT_CLI_CONFIG_PATH


def test_default_values():
    config = CliConfig()
    assert config.browser_api_config_path == DEFAULT_BROWSER_API_CONFIG_PATH
    assert config.default_format == "table"


def test_to_dict_defaults_omitted():
    config = CliConfig()
    d = config.to_dict()
    assert d == {}


def test_to_dict_non_defaults_included():
    config = CliConfig(browser_api_config_path="/custom/path.json", default_format="json")
    d = config.to_dict()
    assert d["browser_api_config_path"] == "/custom/path.json"
    assert d["default_format"] == "json"


def test_from_dict_roundtrip():
    config = CliConfig(browser_api_config_path="/custom/path.json", default_format="tsv")
    restored = CliConfig.from_dict(config.to_dict())
    assert restored.browser_api_config_path == config.browser_api_config_path
    assert restored.default_format == config.default_format


def test_from_dict_defaults_on_empty():
    config = CliConfig.from_dict({})
    assert config.browser_api_config_path == DEFAULT_BROWSER_API_CONFIG_PATH
    assert config.default_format == "table"


def test_save_and_load(tmp_path):
    config = CliConfig(browser_api_config_path="/custom/path.json", default_format="json")
    save_path = tmp_path / "cli.json"
    config.save(save_path)

    assert save_path.exists()
    # Check file permissions are 0o600
    mode = stat.S_IMODE(os.stat(save_path).st_mode)
    assert mode == 0o600

    loaded = CliConfig.load(save_path)
    assert loaded.browser_api_config_path == config.browser_api_config_path
    assert loaded.default_format == config.default_format


def test_load_nonexistent_returns_defaults(tmp_path):
    path = tmp_path / "nonexistent.json"
    config = CliConfig.load(path)
    assert config.browser_api_config_path == DEFAULT_BROWSER_API_CONFIG_PATH
    assert config.default_format == "table"


def test_save_creates_parent_dirs(tmp_path):
    path = tmp_path / "deep" / "nested" / "cli.json"
    config = CliConfig()
    config.save(path)
    assert path.exists()


def test_save_defaults_writes_empty_dict(tmp_path):
    config = CliConfig()
    path = tmp_path / "cli.json"
    config.save(path)
    with open(path) as f:
        data = json.load(f)
    assert data == {}
