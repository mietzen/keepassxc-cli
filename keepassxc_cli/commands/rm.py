from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import ensure_scheme, print_result

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("rm", parents=parents, help="Delete an entry")
    p.add_argument("url", help="URL of the entry to delete")
    p.add_argument("--uuid", default=None, help="UUID to disambiguate when URL matches multiple entries")
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
    entries = client.get_logins(ensure_scheme(args.url))
    if not entries:
        logger.error("No entries found for: %s", args.url)
        return 1

    if args.uuid is not None:
        entry = next((e for e in entries if e.uuid == args.uuid), None)
        if entry is None:
            logger.error("Entry %s not found for URL: %s", args.uuid, args.url)
            return 1
    elif len(entries) == 1:
        entry = entries[0]
    else:
        logger.error(
            "Multiple entries found for %s \u2014 specify --uuid to disambiguate:",
            args.url,
        )
        for e in entries:
            print(f"  {e.uuid}  {e.login}  ({e.name})")
        return 1

    label = f"{entry.name} ({args.url})"
    if not args.yes:
        answer = input(f"Delete entry {label}? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    client.delete_entry(entry.uuid)
    print_result("Entry deleted.", fmt)
    return 0
