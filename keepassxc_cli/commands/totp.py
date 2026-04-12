from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_totp


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("totp", parents=parents, help="Get TOTP code for an entry")
    p.add_argument("url", help="URL to look up")
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
    entries = client.get_logins(args.url)
    if not entries:
        print(f"No entries found for: {args.url}", file=sys.stderr)
        return 1
    entry = entries[0]
    totp = client.get_totp(entry.uuid)
    if totp is None:
        print(f"No TOTP configured for: {entry.name}", file=sys.stderr)
        return 1
    print_totp(totp, fmt)
    return 0
