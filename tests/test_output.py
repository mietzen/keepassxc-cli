from __future__ import annotations

import json

import pytest

from keepassxc_browser_api import Entry, Group
from keepassxc_cli.output import (
    print_entries,
    print_groups,
    print_entry_detail,
    print_totp,
    print_password,
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


@pytest.fixture
def sample_group():
    child = Group(uuid="child-uuid", name="Personal", children=[])
    return Group(uuid="root-uuid", name="Root", children=[child])


class TestPrintEntries:
    def test_table_format(self, capsys, sample_entry):
        print_entries([sample_entry], fmt="table")
        out = capsys.readouterr().out
        assert "GitHub" in out
        assert "user@example.com" in out
        assert "Root" in out
        assert "abcdef12…" in out  # truncated UUID (8 chars + ellipsis)

    def test_json_format(self, capsys, sample_entry):
        print_entries([sample_entry], fmt="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["name"] == "GitHub"
        assert data[0]["login"] == "user@example.com"
        assert data[0]["password"] == "***"

    def test_json_format_show_password(self, capsys, sample_entry):
        print_entries([sample_entry], fmt="json", show_password=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["password"] == "s3cr3t"

    def test_table_format_multiple_entries(self, capsys, sample_entry):
        entries = [sample_entry, sample_entry]
        print_entries(entries, fmt="table")
        out = capsys.readouterr().out
        assert out.count("GitHub") == 2


class TestPrintGroups:
    def test_table_format(self, capsys, sample_group):
        print_groups([sample_group], fmt="table")
        out = capsys.readouterr().out
        assert "Root" in out
        assert "Personal" in out

    def test_json_format(self, capsys, sample_group):
        print_groups([sample_group], fmt="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["name"] == "Root"
        assert data[0]["children"][0]["name"] == "Personal"


class TestPrintEntryDetail:
    def test_table_format(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=False)
        out = capsys.readouterr().out
        assert "GitHub" in out
        assert "user@example.com" in out
        assert "***" in out

    def test_table_format_show_password(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=True)
        out = capsys.readouterr().out
        assert "s3cr3t" in out

    def test_json_format(self, capsys, sample_entry):
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


class TestPrintPassword:
    def test_table_format(self, capsys):
        print_password("mypass", fmt="table")
        assert capsys.readouterr().out.strip() == "mypass"

    def test_json_format(self, capsys):
        print_password("mypass", fmt="json")
        data = json.loads(capsys.readouterr().out)
        assert data["password"] == "mypass"


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
