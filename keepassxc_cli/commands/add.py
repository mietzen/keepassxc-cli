from __future__ import annotations

import argparse
import getpass
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("add", help="Add a new entry")
    p.add_argument("--url", required=True, help="Entry URL")
    p.add_argument("--username", required=True, help="Username")
    p.add_argument("--password", default=None, help="Password (prompted if omitted)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--group-uuid", default="", help="Target group UUID")
    group.add_argument("--group", default=None, help="Target group path (e.g. 'Work/Projects')")
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

    group_uuid = args.group_uuid

    if args.group is not None:
        groups = client.get_database_groups()
        root = groups[0]
        parts = args.group.split("/")
        current = root.children
        matched = None
        for part in parts:
            matched = next((g for g in current if g.name == part), None)
            if matched is None:
                logger.error("Group not found: %r", args.group)
                return 1
            current = matched.children
        group_uuid = matched.uuid

    client.set_login(
        url=args.url,
        username=args.username,
        password=password,
        group_uuid=group_uuid,
    )
    print("Entry added successfully.")
    return 0
