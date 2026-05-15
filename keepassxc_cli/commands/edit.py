from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "edit",
        help="Edit an existing entry by UUID",
        description=(
            "Edit an existing entry. The UUID must be known (use 'show' to find it).\n"
            "Provide --url so the entry can be resolved; omitted fields are left unchanged."
        ),
    )
    p.add_argument("uuid", help="UUID of the entry to edit")
    p.add_argument("--url", required=True, help="URL of the entry (used to resolve current values)")
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
    # Resolve current entry values via get_logins (no special permission needed)
    entries = client.get_logins(args.url)
    entry = next((e for e in entries if e.uuid == args.uuid), None)
    if entry is None:
        logger.error(
            "Entry %s not found for URL: %s\nHint: use 'keepassxc-cli show <url>' to look up the UUID.",
            args.uuid, args.url,
        )
        return 1

    client.set_login(
        url=args.url,
        username=args.username if args.username is not None else entry.login,
        password=args.password if args.password is not None else entry.password,
        title=args.title if args.title is not None else entry.name,
        uuid=entry.uuid,
        group_uuid=entry.group_uuid,
    )
    print("Entry updated successfully.")
    return 0
