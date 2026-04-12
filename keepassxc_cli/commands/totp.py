from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_totp


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("totp", help="Get TOTP code for an entry")
    p.add_argument("uuid", help="UUID of the entry")
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
    totp = client.get_totp(args.uuid)
    if totp is None:
        print(f"No TOTP for entry: {args.uuid}", file=sys.stderr)
        return 1
    print_totp(totp, fmt)
    return 0
