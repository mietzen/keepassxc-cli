from __future__ import annotations

import json

from keepassxc_browser_api import Entry, Group


def _truncate(s: str, n: int) -> str:
    if len(s) > n:
        return s[: n - 1] + "…"
    return s


def _table_row(cols: list[str], widths: list[int]) -> str:
    return "| " + " | ".join(v.ljust(w) for v, w in zip(cols, widths)) + " |"


def _table_sep(widths: list[int]) -> str:
    return "+-" + "-+-".join("-" * w for w in widths) + "-+"


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = _table_sep(widths)
    print(sep)
    print(_table_row(headers, widths))
    print(sep)
    for row in rows:
        print(_table_row(row, widths))
    print(sep)


def print_entries(entries: list[Entry], fmt: str = "table", show_password: bool = False) -> None:
    if fmt == "json":
        data = [
            {
                "uuid": e.uuid,
                "name": e.name,
                "login": e.login,
                "password": e.password if show_password else "***",
                "url": next((sf.get("KPH: url", "") for sf in e.string_fields if "KPH: url" in sf), ""),
                "group": e.group,
            }
            for e in entries
        ]
        print(json.dumps(data, indent=2))
        return

    # table
    headers = ["UUID", "Title", "Username", "URL", "Group"]
    rows = []
    for e in entries:
        url = next((sf.get("KPH: url", "") for sf in e.string_fields if "KPH: url" in sf), "")
        rows.append([_truncate(e.uuid, 9), e.name, e.login, url, e.group])
    _print_table(headers, rows)


def _print_group_tree(group: Group, indent: int = 0) -> None:
    prefix = "  " * indent
    print(f"{prefix}{group.name}  [{_truncate(group.uuid, 9)}]")
    for child in group.children:
        _print_group_tree(child, indent + 1)


def print_groups(groups: list[Group], fmt: str = "table") -> None:
    if fmt == "json":
        def _g2d(g: Group) -> dict:
            return {"uuid": g.uuid, "name": g.name, "children": [_g2d(c) for c in g.children]}
        print(json.dumps([_g2d(g) for g in groups], indent=2))
        return

    for g in groups:
        _print_group_tree(g)


def print_entry_detail(entry: Entry, fmt: str = "table", show_password: bool = False) -> None:
    password = entry.password if show_password else "***"
    totp = entry.totp if show_password else None
    if fmt == "json":
        data = {
            "uuid": entry.uuid,
            "name": entry.name,
            "login": entry.login,
            "password": password,
            "group": entry.group,
            "group_uuid": entry.group_uuid,
            "string_fields": entry.string_fields,
        }
        if totp is not None:
            data["totp"] = totp
        print(json.dumps(data, indent=2))
        return

    print(f"UUID:       {entry.uuid}")
    print(f"Title:      {entry.name}")
    print(f"Username:   {entry.login}")
    print(f"Password:   {password}")
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


def print_password(password: str, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps({"password": password}, indent=2))
        return
    print(password)


def print_status(info: dict, fmt: str = "table") -> None:
    if fmt == "json":
        print(json.dumps(info, indent=2))
        return
    for k, v in info.items():
        print(f"{k}: {v}")
