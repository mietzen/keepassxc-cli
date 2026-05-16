from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import ensure_scheme

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("clip", parents=parents, help="Copy a field to clipboard")
    p.add_argument("url", help="URL to look up")
    p.add_argument(
        "field",
        choices=["password", "username", "totp"],
        help="Field to copy: password, username, or totp",
    )
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
    try:
        import pyperclip
    except ImportError:
        logger.error("pyperclip is required for clipboard support. Install it with: pip install pyperclip")
        return 1

    entries = client.get_logins(ensure_scheme(args.url))
    if not entries:
        logger.warning("No entries found for: %s", args.url)
        return 1

    entry = entries[0]

    if args.field == "password":
        value = entry.password
    elif args.field == "username":
        value = entry.login
    elif args.field == "totp":
        value = client.get_totp(entry.uuid)
        if value is None:
            logger.warning("No TOTP configured for: %s", entry.name)
            return 1
    else:
        logger.error("Unknown field: %s", args.field)
        return 1

    pyperclip.copy(value)
    print(f"Copied {args.field} to clipboard.")
    return 0
