from __future__ import annotations

import json

from keepassxc_browser_api import Entry


def print_entry_detail(entry: Entry, fmt: str = "table", show_password: bool = False) -> None:
    totp = entry.totp if show_password else None
    if fmt == "json":
        data = {
            "uuid": entry.uuid,
            "name": entry.name,
            "login": entry.login,
            "group": entry.group,
            "group_uuid": entry.group_uuid,
            "string_fields": entry.string_fields,
        }
        if show_password:
            data["password"] = entry.password
            if totp is not None:
                data["totp"] = totp
        print(json.dumps(data, indent=2))
        return

    print(f"UUID:       {entry.uuid}")
    print(f"Title:      {entry.name}")
    print(f"Username:   {entry.login}")
    if show_password:
        print(f"Password:   {entry.password}")
    if totp:
        print(f"TOTP:       {totp}")
    if entry.group:
        print(f"Group:      {entry.group}")
    if entry.group_uuid:
        print(f"Group UUID: {entry.group_uuid}")
    if entry.string_fields:
        for sf in entry.string_fields:
            for k, v in sf.items():
                print(f"{k}: {v}")


def print_totp(totp: str, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps({"totp": totp}, indent=2))
        return
    print(totp)


def print_status(info: dict, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps(info, indent=2))
        return
    for k, v in info.items():
        print(f"{k}: {v}")
