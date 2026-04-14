from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

from keepassxc_browser_api import Entry, Group, BrowserConfig, Association


def make_entry(
    uuid: str = "abcdef12-0000-0000-0000-000000000000",
    name: str = "Test Entry",
    login: str = "user@example.com",
    password: str = "s3cr3t",
    totp: str = "",
    group: str = "Root",
    group_uuid: str = "root-uuid-0000-0000-0000-000000000000",
    string_fields: list[dict[str, str]] | None = None,
) -> Entry:
    return Entry(
        uuid=uuid,
        name=name,
        login=login,
        password=password,
        totp=totp,
        group=group,
        group_uuid=group_uuid,
        string_fields=string_fields or [],
    )


def make_group(
    uuid: str = "root-uuid-0000-0000-0000-000000000000",
    name: str = "Root",
    children: list[Group] | None = None,
) -> Group:
    return Group(uuid=uuid, name=name, children=children or [])


@pytest.fixture
def mock_entry():
    return make_entry


@pytest.fixture
def mock_group():
    return make_group


@pytest.fixture
def mock_browser_config():
    assoc = Association(id="test-id", id_key="test-id-key", key="test-key")
    config = BrowserConfig(
        client_public_key="pub",
        client_secret_key="sec",
        unlock_timeout=30,
        associations={"test-id": assoc},
    )
    return config


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.setup.return_value = True
    client.connect.return_value = True
    client.disconnect.return_value = None
    client.ensure_unlocked.return_value = True
    client.test_associate.return_value = True
    client.get_logins.return_value = [make_entry()]
    client.set_login.return_value = True
    client.create_group.return_value = make_group(uuid="new-uuid", name="NewGroup")
    client.get_totp.return_value = "123456"
    client.delete_entry.return_value = True
    client.lock_database.return_value = True
    return client
