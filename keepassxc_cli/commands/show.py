from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_entry_detail


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("show", parents=parents, help="Show entries matching a URL")
    p.add_argument("url", help="URL or search string")
    p.add_argument("-p", "--show-password", action="store_true", help="Reveal password and TOTP")
    p.add_argument("--show-kph-prefix", action="store_true", help="Keep 'KPH: ' prefix on custom string field names")
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
    for entry in entries:
        print_entry_detail(entry, fmt, show_password=args.show_password, show_kph_prefix=getattr(args, "show_kph_prefix", False))
        if fmt == "table" and len(entries) > 1:
            print()
    return 0
