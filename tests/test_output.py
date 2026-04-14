from __future__ import annotations

import json

import pytest

from keepassxc_browser_api import Entry
from keepassxc_cli.output import (
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
        assert "KPH: " not in out
        assert "url: https://github.com" in out

    def test_table_format_show_password(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=True)
        out = capsys.readouterr().out
        assert "s3cr3t" in out
        assert "Password:" in out
        assert "KPH: " not in out

    def test_table_format_show_kph_prefix(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="table", show_password=False, show_kph_prefix=True)
        out = capsys.readouterr().out
        assert "KPH: url: https://github.com" in out

    def test_json_format_hidden(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="json", show_password=False)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["name"] == "GitHub"
        assert "password" not in data
        assert data["string_fields"] == [{"url": "https://github.com"}]

    def test_json_format_show_password(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="json", show_password=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["name"] == "GitHub"
        assert data["password"] == "s3cr3t"
        assert data["string_fields"] == [{"url": "https://github.com"}]

    def test_json_format_show_kph_prefix(self, capsys, sample_entry):
        print_entry_detail(sample_entry, fmt="json", show_password=False, show_kph_prefix=True)
        data = json.loads(capsys.readouterr().out)
        assert data["string_fields"] == [{"KPH: url": "https://github.com"}]


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
