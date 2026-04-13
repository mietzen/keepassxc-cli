from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_entries


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser(
        "search",
        parents=parents,
        help="Search all database entries by title, username, or URL",
        description=(
            "Search all entries in the open database (client-side filter).\n\n"
            "NOTE: requires 'AllowGetDatabaseEntriesRequest=true' in the KeePassXC ini file.\n"
            "See the error message for the exact file path on your platform."
        ),
    )
    p.add_argument("query", help="Search query (case-insensitive match on title, username, or URL)")
    p.add_argument("-p", "--show-password", action="store_true", help="Reveal passwords")
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
    query = args.query.lower()
    all_entries = client.get_database_entries()
    matches = [
        e for e in all_entries
        if query in e.name.lower()
        or query in e.login.lower()
        or any(query in v.lower() for sf in e.string_fields for v in sf.values() if v is not None)
    ]
    if not matches:
        print(f"No entries found matching: {args.query}", file=sys.stderr)
        return 1
    print_entries(matches, fmt, show_password=args.show_password)
    return 0
