from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("clip", help="Copy a field to clipboard")
    p.add_argument(
        "field",
        choices=["password", "username", "totp"],
        help="Field to copy: password, username, or totp",
    )
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
    try:
        import pyperclip
    except ImportError:
        print("Error: pyperclip is required for clipboard support. Install it with: pip install pyperclip", file=sys.stderr)
        return 1

    entries = client.get_logins(args.url)
    if not entries:
        print(f"No entries found for: {args.url}", file=sys.stderr)
        return 1

    entry = entries[0]

    if args.field == "password":
        value = entry.password
    elif args.field == "username":
        value = entry.login
    elif args.field == "totp":
        value = client.get_totp(entry.uuid)
        if value is None:
            print(f"No TOTP configured for: {entry.name}", file=sys.stderr)
            return 1
    else:
        print(f"Unknown field: {args.field}", file=sys.stderr)
        return 1

    pyperclip.copy(value)
    print(f"Copied {args.field} to clipboard.")
    return 0
