from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import ensure_scheme

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("rm", help="Delete an entry")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--uuid", default=None, help="UUID of the entry to delete")
    group.add_argument("--url", default=None, help="URL of the entry to delete (must match exactly one entry)")
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
    if args.uuid is not None:
        target_uuid = args.uuid
        label = args.uuid
    else:
        entries = client.get_logins(ensure_scheme(args.url))
        if not entries:
            logger.error("No entries found for: %s", args.url)
            return 1
        if len(entries) > 1:
            logger.error(
                "Multiple entries found for %s \u2014 specify --uuid to disambiguate:",
                args.url,
            )
            for e in entries:
                print(f"  {e.uuid}  {e.login}  ({e.name})")
            return 1
        target_uuid = entries[0].uuid
        label = f"{entries[0].name} ({args.url})"

    if not args.yes:
        answer = input(f"Delete entry {label}? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    client.delete_entry(target_uuid)
    print("Entry deleted.")
    return 0
