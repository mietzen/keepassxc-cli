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
    p = subparsers.add_parser(
        "edit",
        parents=parents,
        help="Edit an existing entry",
        description=(
            "Edit an existing entry by URL. Omitted fields are left unchanged.\n"
            "If the URL matches multiple entries, specify --uuid to disambiguate."
        ),
    )
    p.add_argument("url", help="URL of the entry")
    p.add_argument("--uuid", default=None, help="UUID of the entry (required when URL matches multiple entries)")
    p.add_argument("--username", default=None, help="New username")
    p.add_argument("--password", default=None, help="New password")
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
    url = ensure_scheme(args.url)
    entries = client.get_logins(url)

    if not entries:
        logger.error("No entries found for: %s", args.url)
        return 1

    if args.uuid is not None:
        entry = next((e for e in entries if e.uuid == args.uuid), None)
        if entry is None:
            logger.error(
                "Entry %s not found for URL: %s",
                args.uuid, args.url,
            )
            return 1
    elif len(entries) == 1:
        entry = entries[0]
    else:
        logger.error(
            "Multiple entries found for %s — specify --uuid to disambiguate:",
            args.url,
        )
        for e in entries:
            print(f"  {e.uuid}  {e.login}  ({e.name})")
        return 1

    client.set_login(
        url=url,
        username=args.username if args.username is not None else entry.login,
        password=args.password if args.password is not None else entry.password,
        uuid=entry.uuid,
        group_uuid=entry.group_uuid,
    )
    print_result("Entry updated.", fmt)
    return 0
