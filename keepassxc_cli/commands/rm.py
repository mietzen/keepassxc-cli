from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("rm", help="Delete an entry by UUID")
    p.add_argument("uuid", help="UUID of the entry to delete")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
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
    if not args.yes:
        answer = input(f"Delete entry {args.uuid}? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    success = client.delete_entry(args.uuid)
    if success:
        print("Entry deleted.")
        return 0
    else:
        print("Failed to delete entry.", file=sys.stderr)
        return 1
