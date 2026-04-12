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
        help="Search database entries by URL or hostname",
    )
    p.add_argument("query", help="URL or hostname to search for")
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
    entries = client.get_logins(args.query)
    if not entries:
        print(f"No entries found matching: {args.query}", file=sys.stderr)
        return 1
    print_entries(entries, fmt, show_password=args.show_password)
    return 0
