from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from keepassxc_browser_api import Entry, BrowserConfig, Association
from keepassxc_browser_api.exceptions import ConnectionError, DatabaseLockedError, ProtocolError
from keepassxc_cli.config import CliConfig
from keepassxc_cli.commands import (
    setup, status, show, add, edit, rm, totp, clip, lock, mkdir, group_uuid, version,
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
        "group": None,
        "uuid": "abcdef12-0000-0000-0000-000000000000",
        "name": "NewGroup",
        "path": "Work",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- setup ---

class TestSetupCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.setup.return_value = None
        args = make_args()
        rc = setup.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.setup.assert_called_once()

    def test_failure_propagates(self, mock_client, cli_config, browser_config, browser_config_path):
        mock_client.setup.side_effect = ConnectionError("KeePassXC not running")
        args = make_args()
        with pytest.raises(ConnectionError):
            setup.run(mock_client, args, cli_config, browser_config, browser_config_path)


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
        mock_client.connect.side_effect = ConnectionError("not available")
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

    def test_no_entries(self, mock_client, cli_config, browser_config, browser_config_path, caplog):
        mock_client.get_logins.return_value = []
        args = make_args(url="https://notfound.com")
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("No entries" in r.message for r in caplog.records)

    def test_url_no_scheme_prefixed(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        args = make_args(url="example.com", show_password=False)
        rc = show.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.get_logins.assert_called_once_with("https://example.com")
        assert any("no scheme" in r.message.lower() for r in caplog.records)


# --- add ---

class TestAddCommand:
    def test_success(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.set_login.return_value = True
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="", group=None)
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.set_login.assert_called_once()
        assert "added" in capsys.readouterr().out.lower()

    def test_group_path_resolved(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        from keepassxc_browser_api import Group
        projects = mock_group(uuid="proj-uuid", name="Projects")
        work = mock_group(uuid="work-uuid", name="Work", children=[projects])
        root = mock_group(uuid="root-uuid", name="Root", children=[work])
        mock_client.get_database_groups.return_value = [root]
        mock_client.set_login.return_value = True
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="", group="Work/Projects")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        call_kwargs = mock_client.set_login.call_args.kwargs
        assert call_kwargs["group_uuid"] == "proj-uuid"

    def test_group_path_not_found(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_group):
        root = mock_group(uuid="root-uuid", name="Root", children=[])
        mock_client.get_database_groups.return_value = [root]
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="", group="NonExistent")
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("not found" in r.message.lower() for r in caplog.records)

    def test_url_no_scheme_prefixed(self, mock_client, cli_config, browser_config, browser_config_path, caplog):
        mock_client.set_login.return_value = True
        args = make_args(url="example.com", username="u", password="p", group_uuid="", group=None)
        rc = add.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        call_kwargs = mock_client.set_login.call_args.kwargs
        assert call_kwargs["url"] == "https://example.com"
        assert any("no scheme" in r.message.lower() for r in caplog.records)

    def test_failure_propagates(self, mock_client, cli_config, browser_config, browser_config_path):
        mock_client.set_login.side_effect = ProtocolError("access denied", error_code=6)
        args = make_args(url="https://example.com", username="u", password="p", group_uuid="", group=None)
        with pytest.raises(ProtocolError):
            add.run(mock_client, args, cli_config, browser_config, browser_config_path)


# --- edit ---

class TestEditCommand:
    def test_uuid_specified_and_updated(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        mock_client.set_login.return_value = True
        args = make_args(uuid=entry.uuid, url="https://example.com", username="newuser", password=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "updated" in capsys.readouterr().out.lower()
        mock_client.set_login.assert_called_once()
        call_kwargs = mock_client.set_login.call_args.kwargs
        assert "title" not in call_kwargs

    def test_no_uuid_single_match_auto_selected(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        mock_client.set_login.return_value = True
        args = make_args(uuid=None, url="https://example.com", username="newuser", password=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        assert "updated" in capsys.readouterr().out.lower()

    def test_no_uuid_multiple_matches_error(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_entry):
        e1 = mock_entry(uuid="uuid-1", login="alice")
        e2 = mock_entry(uuid="uuid-2", login="bob")
        mock_client.get_logins.return_value = [e1, e2]
        args = make_args(uuid=None, url="https://example.com", username="newuser", password=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("multiple" in r.message.lower() for r in caplog.records)

    def test_uuid_not_in_results(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_entry):
        entry = mock_entry()
        mock_client.get_logins.return_value = [entry]
        args = make_args(uuid="nonexistent-uuid", url="https://example.com", username=None, password=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("not found" in r.message.lower() for r in caplog.records)

    def test_no_entries_found(self, mock_client, cli_config, browser_config, browser_config_path, caplog):
        mock_client.get_logins.return_value = []
        args = make_args(uuid=None, url="https://example.com", username=None, password=None)
        rc = edit.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("no entries" in r.message.lower() for r in caplog.records)


# --- rm ---

class TestRmCommand:
    def test_uuid_with_yes_flag(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        mock_client.delete_entry.return_value = True
        args = make_args(uuid="some-uuid", url=None, yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.delete_entry.assert_called_once_with("some-uuid")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_url_single_match_deletes(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_entry):
        entry = mock_entry(uuid="url-resolved-uuid")
        mock_client.get_logins.return_value = [entry]
        mock_client.delete_entry.return_value = True
        args = make_args(uuid=None, url="https://example.com", yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.delete_entry.assert_called_once_with("url-resolved-uuid")

    def test_url_multiple_matches_error(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_entry):
        e1 = mock_entry(uuid="uuid-1", login="alice")
        e2 = mock_entry(uuid="uuid-2", login="bob")
        mock_client.get_logins.return_value = [e1, e2]
        args = make_args(uuid=None, url="https://example.com", yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("multiple" in r.message.lower() for r in caplog.records)

    def test_url_no_entries_error(self, mock_client, cli_config, browser_config, browser_config_path, caplog):
        mock_client.get_logins.return_value = []
        args = make_args(uuid=None, url="https://notfound.com", yes=True)
        rc = rm.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("no entries" in r.message.lower() for r in caplog.records)

    def test_failure_propagates(self, mock_client, cli_config, browser_config, browser_config_path):
        mock_client.delete_entry.side_effect = ProtocolError("access denied", error_code=6)
        args = make_args(uuid="some-uuid", url=None, yes=True)
        with pytest.raises(ProtocolError):
            rm.run(mock_client, args, cli_config, browser_config, browser_config_path)


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

    def test_pyperclip_missing(self, mock_client, cli_config, browser_config, browser_config_path, caplog):
        args = make_args(url="https://example.com", field="password")
        with patch.dict("sys.modules", {"pyperclip": None}):
            rc = clip.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("pyperclip" in r.message for r in caplog.records)


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
        args = make_args(name="MyGroup")
        rc = mkdir.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "MyGroup" in out

    def test_path_syntax(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        new_group = mock_group(uuid="new-uuid", name="Projects")
        mock_client.create_group.return_value = new_group
        args = make_args(name="Work/Projects")
        rc = mkdir.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        mock_client.create_group.assert_called_once_with("Work/Projects")

    def test_failure_propagates(self, mock_client, cli_config, browser_config, browser_config_path):
        mock_client.create_group.side_effect = ConnectionError("KeePassXC not running")
        args = make_args(name="MyGroup")
        with pytest.raises(ConnectionError):
            mkdir.run(mock_client, args, cli_config, browser_config, browser_config_path)


# --- group-uuid ---


class TestGroupUuidCommand:
    def _make_tree(self, mock_group):
        from keepassxc_browser_api import Group
        projects = mock_group(uuid="projects-uuid", name="Projects")
        work = mock_group(uuid="work-uuid", name="Work", children=[projects])
        root = mock_group(uuid="root-uuid", name="Root", children=[work])
        return [root]

    def test_found_top_level(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        mock_client.get_database_groups.return_value = self._make_tree(mock_group)
        args = make_args(path="Work")
        rc = group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "work-uuid" in out
        assert "Work" in out

    def test_found_nested_path(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        mock_client.get_database_groups.return_value = self._make_tree(mock_group)
        args = make_args(path="Work/Projects")
        rc = group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "projects-uuid" in out

    def test_not_found(self, mock_client, cli_config, browser_config, browser_config_path, caplog, mock_group):
        mock_client.get_database_groups.return_value = self._make_tree(mock_group)
        args = make_args(path="Nonexistent")
        rc = group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1
        assert any("not found" in r.message.lower() for r in caplog.records)

    def test_not_found_mid_path(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        mock_client.get_database_groups.return_value = self._make_tree(mock_group)
        args = make_args(path="Work/Nope/Projects")
        rc = group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 1

    def test_json_output(self, mock_client, cli_config, browser_config, browser_config_path, capsys, mock_group):
        import json
        mock_client.get_database_groups.return_value = self._make_tree(mock_group)
        args = make_args(path="Work/Projects")
        rc = group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path, fmt="json")
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["path"] == "Work/Projects"
        assert data["name"] == "Projects"
        assert data["uuid"] == "projects-uuid"

    def test_get_database_groups_failure_propagates(self, mock_client, cli_config, browser_config, browser_config_path, mock_group):
        mock_client.get_database_groups.side_effect = ConnectionError("KeePassXC not running")
        args = make_args(path="Work")
        with pytest.raises(ConnectionError):
            group_uuid.run(mock_client, args, cli_config, browser_config, browser_config_path)

# --- version ---


class TestVersionCommand:
    def test_prints_version(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        with patch("keepassxc_cli.commands.version.version", return_value="1.3.0"):
            args = make_args()
            rc = version.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "keepassxc-cli" in out
        assert "1.3.0" in out

    def test_package_not_found(self, mock_client, cli_config, browser_config, browser_config_path, capsys):
        from importlib.metadata import PackageNotFoundError
        with patch("keepassxc_cli.commands.version.version", side_effect=PackageNotFoundError):
            args = make_args()
            rc = version.run(mock_client, args, cli_config, browser_config, browser_config_path)
        assert rc == 0
        out = capsys.readouterr().out
        assert "unknown" in out


# --- exit codes ---

class TestExitCodes:
    """Test that __main__.main() maps exceptions to the correct exit codes."""

    def _run_main(self, exception, monkeypatch, capsys, tmp_path):
        from keepassxc_cli.__main__ import main

        config_path = tmp_path / "cli.json"
        monkeypatch.setattr("sys.argv", [
            "keepassxc-cli", "--config", str(config_path),
            "show", "https://example.com",
        ])

        mock_client_instance = MagicMock()
        mock_client_instance.get_logins.side_effect = exception

        with patch("keepassxc_cli.__main__.BrowserClient", return_value=mock_client_instance):
            with patch("keepassxc_cli.__main__.BrowserConfig"):
                with patch("keepassxc_cli.__main__.CliConfig"):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        return exc_info.value.code, capsys.readouterr()

    def test_connection_error_rc2(self, monkeypatch, capsys, tmp_path):
        rc, out = self._run_main(ConnectionError("not running"), monkeypatch, capsys, tmp_path)
        assert rc == 2
        assert "Error:" in out.err

    def test_database_locked_rc3(self, monkeypatch, capsys, tmp_path):
        rc, out = self._run_main(DatabaseLockedError("locked"), monkeypatch, capsys, tmp_path)
        assert rc == 3

    def test_access_denied_rc4(self, monkeypatch, capsys, tmp_path):
        rc, out = self._run_main(ProtocolError("denied", error_code=6), monkeypatch, capsys, tmp_path)
        assert rc == 4

    def test_access_denied_code19_rc4(self, monkeypatch, capsys, tmp_path):
        rc, out = self._run_main(ProtocolError("denied", error_code=19), monkeypatch, capsys, tmp_path)
        assert rc == 4

    def test_other_protocol_error_rc1(self, monkeypatch, capsys, tmp_path):
        rc, out = self._run_main(ProtocolError("other error", error_code=7), monkeypatch, capsys, tmp_path)
        assert rc == 1
