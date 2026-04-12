from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("edit", help="Edit an existing entry by UUID")
    p.add_argument("uuid", help="UUID of the entry to edit")
    p.add_argument("--url", default=None, help="New URL")
    p.add_argument("--username", default=None, help="New username")
    p.add_argument("--password", default=None, help="New password")
    p.add_argument("--title", default=None, help="New title")
    p.set_defaults(func=run)


def run(
    client: BrowserClient,
    args: argparse.Namespace,
    cli_config: CliConfig,
    browser_config: BrowserConfig,
    browser_config_path: Path,
    *,
    fmt: str = "table",
) -> int:
    all_entries = client.get_database_entries()
    entry = next((e for e in all_entries if e.uuid == args.uuid), None)
    if entry is None:
        print(f"Entry not found: {args.uuid}", file=sys.stderr)
        return 1

    # Determine the URL to use for set_login (required by the API)
    url = args.url or next(
        (sf.get("KPH: url", "") for sf in entry.string_fields if "KPH: url" in sf),
        "",
    )

    success = client.set_login(
        url=url,
        username=args.username if args.username is not None else entry.login,
        password=args.password if args.password is not None else entry.password,
        title=args.title if args.title is not None else entry.name,
        uuid=entry.uuid,
        group_uuid=entry.group_uuid,
    )
    if success:
        print("Entry updated successfully.")
        return 0
    else:
        print("Failed to update entry.", file=sys.stderr)
        return 1
