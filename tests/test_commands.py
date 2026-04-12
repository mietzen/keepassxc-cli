from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from keepassxc_browser_api import Entry, Group, BrowserConfig, Association
from keepassxc_cli.config import CliConfig
from keepassxc_cli.commands import (
    setup, status, show, search, ls, add, edit, rm, totp, clip, generate, lock, mkdir,
)


@pytest.fixture
def cli_config():
    return CliConfig()


@pytest.fixture
def browser_config(mock_browser_config):
    return mock_browser_config


@pytest.fixture
def browser_config_path(tmp_path):
    return tmp_path / "browser-api.json"


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "show_password": False,
        "yes": False,
        "groups": False,
        "field": "password",
        "clip": False,
        "url": "https://example.com",
        "username": "user",
        "password": "pass",
        "title": "Example",
        "group_uuid": "",
        "uuid": "abcdef12-0000-0000-0000-000000000000",
        "query": "test",
        "name": "NewGroup",
        "parent_uuid": "",
        "length": 20,
        "no_numbers": False,
        "no_lowercase": False,
        "no_uppercase": False,
        "symbols": False,
        "special": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- setup ---

class TestSetupCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path):
        mock_client.setup.return_value = True
        args = make_args()
        rc = setup.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.setup.assert_called_once()

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.setup.return_value = False
        args = make_args()
        rc = setup.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "Failed" in capsys.readouterr().err


# --- status ---

class TestStatusCommand:
    def test_connected_and_associated(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.connect.return_value = True
        mock_client.test_associate.return_value = True
        args = make_args()
        rc = status.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "yes" in out

    def test_not_connected(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.connect.return_value = False
        args = make_args()
        rc = status.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        out = capsys.readouterr().out
        assert "no" in out

    def test_not_associated(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.connect.return_value = True
        mock_client.test_associate.return_value = False
        args = make_args()
        rc = status.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "no" in out


# --- show ---

class TestShowCommand:
    def test_found_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="https://example.com", show_password=False)
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Test Entry" in out

    def test_no_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_logins.return_value = []
        args = make_args(url="https://notfound.com")
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "No entries" in capsys.readouterr().err


# --- search ---

class TestSearchCommand:
    def test_matches_found(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry(name="GitHub", login="user@github.com")
        mock_client.get_database_entries.return_value = [entry]
        args = make_args(query="github")
        rc = search.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "GitHub" in capsys.readouterr().out

    def test_no_matches(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry(name="GitHub")
        mock_client.get_database_entries.return_value = [entry]
        args = make_args(query="zzznomatch")
        rc = search.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "No entries" in capsys.readouterr().err


# --- ls ---

class TestLsCommand:
    def test_list_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        mock_client.get_database_entries.return_value = [mock_entry()]
        args = make_args(groups=False)
        rc = ls.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "Test Entry" in capsys.readouterr().out

    def test_list_groups(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        mock_client.get_database_groups.return_value = [mock_group()]
        args = make_args(groups=True)
        rc = ls.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "Root" in capsys.readouterr().out


# --- add ---

class TestAddCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.set_login.return_value = True
        args = make_args(url="https://example.com", username="u", password="p", title="T", group_uuid="")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.set_login.assert_called_once()
        assert "added" in capsys.readouterr().out.lower()

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.set_login.return_value = False
        args = make_args(url="https://example.com", username="u", password="p", title="T", group_uuid="")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1


# --- edit ---

class TestEditCommand:
    def test_entry_found_and_updated(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_database_entries.return_value = [entry]
        mock_client.set_login.return_value = True
        args = make_args(uuid=entry.uuid, url=None, username="newuser", password=None, title=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "updated" in capsys.readouterr().out.lower()

    def test_entry_not_found(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_database_entries.return_value = []
        args = make_args(uuid="nonexistent-uuid", url=None, username=None, password=None, title=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "not found" in capsys.readouterr().err.lower()


# --- rm ---

class TestRmCommand:
    def test_with_yes_flag(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.delete_entry.return_value = True
        args = make_args(uuid="some-uuid", yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.delete_entry.assert_called_once_with("some-uuid")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.delete_entry.return_value = False
        args = make_args(uuid="some-uuid", yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1


# --- totp ---

class TestTotpCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_totp.return_value = "654321"
        args = make_args(uuid="some-uuid")
        rc = totp.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "654321" in capsys.readouterr().out

    def test_no_totp(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_totp.return_value = None
        args = make_args(uuid="some-uuid")
        rc = totp.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1


# --- clip ---

class TestClipCommand:
    def test_password_copied(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry(password="secret123")
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="https://example.com", field="password")
        with patch.dict("sys.modules", {"pyperclip": MagicMock()}):
            import pyperclip
            rc = clip.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0

    def test_no_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_logins.return_value = []
        args = make_args(url="https://notfound.com", field="password")
        with patch.dict("sys.modules", {"pyperclip": MagicMock()}):
            rc = clip.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1

    def test_pyperclip_missing(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        args = make_args(url="https://example.com", field="password")
        with patch.dict("sys.modules", {"pyperclip": None}):
            rc = clip.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "pyperclip" in capsys.readouterr().err


# --- generate ---

class TestGenerateCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.generate_password.return_value = "GenPass123!"
        args = make_args(length=20, no_numbers=False, no_lowercase=False, no_uppercase=False, symbols=False, special=False, clip=False)
        rc = generate.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "GenPass123!" in capsys.readouterr().out

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.generate_password.return_value = None
        args = make_args(length=20, no_numbers=False, no_lowercase=False, no_uppercase=False, symbols=False, special=False, clip=False)
        rc = generate.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1

    def test_clip(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.generate_password.return_value = "GenPass123!"
        args = make_args(length=20, no_numbers=False, no_lowercase=False, no_uppercase=False, symbols=False, special=False, clip=True)
        with patch.dict("sys.modules", {"pyperclip": MagicMock()}):
            rc = generate.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0


# --- lock ---

class TestLockCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.lock_database.return_value = True
        args = make_args()
        rc = lock.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "locked" in capsys.readouterr().out.lower()

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.lock_database.return_value = False
        args = make_args()
        rc = lock.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1


# --- mkdir ---

class TestMkdirCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        new_group = mock_group(uuid="new-uuid", name="MyGroup")
        mock_client.create_group.return_value = new_group
        args = make_args(name="MyGroup", parent_uuid="")
        rc = mkdir.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "MyGroup" in out

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.create_group.return_value = None
        args = make_args(name="MyGroup", parent_uuid="")
        rc = mkdir.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
