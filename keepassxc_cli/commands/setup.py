from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("setup", help="Associate with KeePassXC (key exchange)")
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
    success = client.setup()
    if success:
        browser_config.save(browser_config_path)
        print("Successfully associated with KeePassXC.")
        return 0
    else:
        print("Failed to associate with KeePassXC.", file=sys.stderr)
        return 1
