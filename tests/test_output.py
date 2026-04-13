from __future__ import annotations

import json

import pytest

from keepassxc_browser_api import Entry, Group
from keepassxc_cli.output import (
    print_entries,
    print_groups,
    print_entry_detail,
    print_totp,
    print_status,
)


@pytest.fixture
def sample_entry():
    return Entry(
        uuid="abcdef12-0000-0000-0000-000000000000",
        name="GitHub",
        login="user@example.com",
        password="s3cr3t",
        totp="",
        group="Root",
        group_uuid="root-uuid",
        string_fields=[{"KPH: url": "https://github.com"}],
    )


class TestPrintEntryDetail:
    def test_table_format_hidden(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=False)
        out = capsys.readouterr().out
        assert "GitHub" in out
        assert "user@example.com" in out
        assert "Password" not in out
        assert "s3cr3t" not in out

    def test_table_format_show_password(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=True)
        out = capsys.readouterr().out
        assert "s3cr3t" in out
        assert "Password:" in out

    def test_json_format_hidden(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="json", show_password=False)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["name"] == "GitHub"
        assert "password" not in data

    def test_json_format_show_password(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="json", show_password=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["name"] == "GitHub"
        assert data["password"] == "s3cr3t"


class TestPrintTotp:
    def test_table_format(self, capsys):
        print_totp("123456", fmt="table")
        assert capsys.readouterr().out.strip() == "123456"

    def test_json_format(self, capsys):
        print_totp("123456", fmt="json")
        data = json.loads(capsys.readouterr().out)
        assert data["totp"] == "123456"


class TestPrintStatus:
    def test_table_format(self, capsys):
        print_status({"Connected": "yes", "Associated": "no"}, fmt="table")
        out = capsys.readouterr().out
        assert "Connected: yes" in out
        assert "Associated: no" in out

    def test_json_format(self, capsys):
        print_status({"Connected": "yes"}, fmt="json")
        data = json.loads(capsys.readouterr().out)
        assert data["Connected"] == "yes"


class TestPrintEntries:
    def test_table_format(self, capsys):
        entries = [
            Entry(
                uuid="abcdef12-0000-0000-0000-000000000000",
                name="GitHub",
                login="user@example.com",
                password="s3cr3t",
                totp="",
                group="Root",
                group_uuid="root-uuid",
                string_fields=[{"KPH: url": "https://github.com"}],
            )
        ]
        print_entries(entries, fmt="table")
        out = capsys.readouterr().out
        assert "GitHub" in out
        assert "user@example.com" in out
        assert "s3cr3t" not in out

    def test_table_format_show_password(self, capsys):
        entries = [
            Entry(
                uuid="abcdef12-0000-0000-0000-000000000000",
                name="GitHub",
                login="user@example.com",
                password="s3cr3t",
                totp="",
                group="Root",
                group_uuid="root-uuid",
                string_fields=[],
            )
        ]
        # Table format does not include a password column; use JSON for that
        print_entries(entries, fmt="table", show_password=True)
        out = capsys.readouterr().out
        assert "GitHub" in out

    def test_json_format(self, capsys):
        entries = [
            Entry(
                uuid="abcdef12-0000-0000-0000-000000000000",
                name="GitHub",
                login="user@example.com",
                password="s3cr3t",
                totp="",
                group="Root",
                group_uuid="root-uuid",
                string_fields=[],
            )
        ]
        print_entries(entries, fmt="json")
        data = json.loads(capsys.readouterr().out)
        assert data[0]["name"] == "GitHub"
        assert "password" not in data[0]

    def test_json_format_show_password(self, capsys):
        entries = [
            Entry(
                uuid="abcdef12-0000-0000-0000-000000000000",
                name="GitHub",
                login="user@example.com",
                password="s3cr3t",
                totp="",
                group="Root",
                group_uuid="root-uuid",
                string_fields=[],
            )
        ]
        print_entries(entries, fmt="json", show_password=True)
        data = json.loads(capsys.readouterr().out)
        assert data[0]["password"] == "s3cr3t"


class TestPrintGroups:
    def test_table_format(self, capsys):
        groups = [
            Group(
                uuid="root-uuid",
                name="Root",
                children=[Group(uuid="child-uuid", name="Personal", children=[])],
            )
        ]
        print_groups(groups, fmt="table")
        out = capsys.readouterr().out
        assert "Root" in out
        assert "Personal" in out

    def test_json_format(self, capsys):
        groups = [
            Group(
                uuid="root-uuid",
                name="Root",
                children=[Group(uuid="child-uuid", name="Personal", children=[])],
            )
        ]
        print_groups(groups, fmt="json")
        data = json.loads(capsys.readouterr().out)
        assert data[0]["name"] == "Root"
        assert data[0]["children"][0]["name"] == "Personal"
