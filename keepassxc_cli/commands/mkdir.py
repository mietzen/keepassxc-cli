from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_result

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("mkdir", parents=parents, help="Create a new group")
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
    if fmt == "json":
        print(json.dumps({"name": group.name, "uuid": group.uuid}, indent=2))
    else:
        print_result(f"Group created: {group.name} [{group.uuid}]", fmt)
    return 0
