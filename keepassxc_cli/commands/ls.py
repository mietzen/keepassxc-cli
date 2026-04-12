from __future__ import annotations

import argparse
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_entries, print_groups


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser(
        "ls",
        parents=parents,
        help="List all database entries or groups",
        description=(
            "List all entries or groups in the open database.\n\n"
            "NOTE: requires 'Allow access to all entries' to be enabled in\n"
            "KeePassXC → Settings → Browser Integration."
        ),
    )
    p.add_argument("--groups", action="store_true", help="List groups instead of entries")
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
    if args.groups:
        groups = client.get_database_groups()
        print_groups(groups, fmt)
    else:
        entries = client.get_database_entries()
        print_entries(entries, fmt)
    return 0
