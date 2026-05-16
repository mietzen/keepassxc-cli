from __future__ import annotations

import json
import logging

from keepassxc_browser_api import Entry

_KPH_PREFIX = "KPH: "

logger = logging.getLogger(__name__)


def ensure_scheme(url: str) -> str:
    """Return url with a scheme. Prepends https:// with a warning if none is present."""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    logger.warning("URL %r has no scheme, assuming https://", url)
    return "https://" + url


def _strip_kph(key: str) -> str:
    return key[len(_KPH_PREFIX):] if key.startswith(_KPH_PREFIX) else key


def print_entry_detail(
    entry: Entry,
    fmt: str = "table",
    show_password: bool = False,
    show_kph_prefix: bool = False,
) -> None:
    totp = entry.totp if show_password else None

    def _fields() -> list[dict[str, str]]:
        if show_kph_prefix:
            return entry.string_fields
        return [{_strip_kph(k): v for k, v in sf.items()} for sf in entry.string_fields]

    if fmt == "json":
        data = {
            "uuid": entry.uuid,
            "name": entry.name,
            "login": entry.login,
            "group": entry.group,
            "group_uuid": entry.group_uuid,
            "string_fields": _fields(),
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
        for sf in _fields():
            for k, v in sf.items():
                print(f"{k}: {v}")


def print_totp(totp: str, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps({"totp": totp}, indent=2))
        return
    print(totp)


def print_result(message: str, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps({"status": "ok", "message": message}, indent=2))
        return
    print(message)


def print_status(info: dict, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps(info, indent=2))
        return
    for k, v in info.items():
        print(f"{k}: {v}")
