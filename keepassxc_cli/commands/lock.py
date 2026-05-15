from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("lock", help="Lock the KeePassXC database")
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
    success = client.lock_database()
    if success:
        print("Database locked.")
        return 0
    else:
        logger.error("Failed to lock database.")
        return 1
