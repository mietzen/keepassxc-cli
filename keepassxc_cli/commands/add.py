from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("add", help="Add a new entry")
    p.add_argument("--url", required=True, help="Entry URL")
    p.add_argument("--username", required=True, help="Username")
    p.add_argument("--password", default=None, help="Password (prompted if omitted)")
    p.add_argument("--group-uuid", default="", help="Target group UUID")
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
    password = args.password
    if password is None:
        password = getpass.getpass("Password: ")

    success = client.set_login(
        url=args.url,
        username=args.username,
        password=password,
        group_uuid=args.group_uuid,
    )
    if success:
        print("Entry added successfully.")
        return 0
    else:
        print("Failed to add entry.", file=sys.stderr)
        return 1
