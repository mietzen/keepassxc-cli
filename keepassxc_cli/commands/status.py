from __future__ import annotations

import argparse
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig
from keepassxc_browser_api.exceptions import KeePassXCError

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_status


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("status", parents=parents, help="Show KeePassXC connection and association status")
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
    info: dict = {}

    connected = client.connect()
    info["Connected"] = "yes" if connected else "no"

    if not connected:
        print_status(info, fmt)
        return 1

    associated = False
    if browser_config.associations:
        try:
            association = next(iter(browser_config.associations.values()))
            associated = client.test_associate(association)
        except KeePassXCError:
            associated = False

    info["Associated"] = "yes" if associated else "no"
    info["Unlock timeout"] = str(browser_config.unlock_timeout)

    client.disconnect()
    print_status(info, fmt)
    return 0
