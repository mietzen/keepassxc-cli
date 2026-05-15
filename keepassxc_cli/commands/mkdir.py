from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("mkdir", help="Create a new group")
    p.add_argument(
        "name",
        help="Group name or path. Use '/' to create nested groups (e.g. 'Work/Projects').",
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
    group = client.create_group(args.name)
    print(f"Group created: {group.name} [{group.uuid}]")
    return 0
