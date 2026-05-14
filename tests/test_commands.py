from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from keepassxc_browser_api import Entry, BrowserConfig, Association
from keepassxc_cli.config import CliConfig
from keepassxc_cli.commands import (
    setup, status, show, add, edit, rm, totp, clip, lock, mkdir,
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
        "show_kph_prefix": False,
        "yes": False,
        "field": "password",
        "url": "https://example.com",
        "username": "user",
        "password": "pass",
        "group_uuid": "",
        "uuid": "abcdef12-0000-0000-0000-000000000000",
        "name": "NewGroup",
        "parent_uuid": "",
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
        entry = mock_entry(string_fields=[{"KPH: url": "https://github.com"}])
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="https://example.com", show_password=False)
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Test Entry" in out
        assert "Password" not in out
        assert "KPH: " not in out
        assert "url: https://github.com" in out

    def test_found_entries_show_password(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="https://example.com", show_password=True)
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Test Entry" in out
        assert "Password:" in out

    def test_found_entries_show_kph_prefix(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry(string_fields=[{"KPH: url": "https://github.com"}])
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="https://example.com", show_password=False, show_kph_prefix=True)
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "KPH: url: https://github.com" in capsys.readouterr().out

    def test_no_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_logins.return_value = []
        args = make_args(url="https://notfound.com")
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert "No entries" in capsys.readouterr().err


# --- add ---

class TestAddCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.set_login.return_value = True
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.set_login.assert_called_once()
        assert "added" in capsys.readouterr().out.lower()

    def test_failure(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.set_login.return_value = False
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1


# --- edit ---

class TestEditCommand:
    def test_entry_found_and_updated(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        mock_client.set_login.return_value = True
        args = make_args(uuid=entry.uuid, url="https://example.com", username="newuser", password=None, title=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "updated" in capsys.readouterr().out.lower()

    def test_entry_not_found(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_logins.return_value = []
        args = make_args(uuid="nonexistent-uuid", url="https://example.com", username=None, password=None, title=None)
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
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        mock_client.get_totp.return_value = "654321"
        args = make_args(url="https://example.com")
        rc = totp.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "654321" in capsys.readouterr().out

    def test_no_entries(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.get_logins.return_value = []
        args = make_args(url="https://example.com")
        rc = totp.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1

    def test_no_totp(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        mock_client.get_totp.return_value = None
        args = make_args(url="https://example.com")
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
