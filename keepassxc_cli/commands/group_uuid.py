from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser(
        "group-uuid",
        parents=parents,
        help="Look up the UUID of a group by its path",
    )
    p.add_argument(
        "path",
        help="Group path relative to the database root (e.g. 'Work/Projects')",
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
    groups = client.get_database_groups()
    root = groups[0]
    parts = args.path.split("/")

    # Paths are root-relative: traverse root.children, not the root itself.
    current = root.children
    matched = None
    for part in parts:
        matched = next((g for g in current if g.name == part), None)
        if matched is None:
            logger.error("Group not found: %r", args.path)
            return 1
        current = matched.children

    if fmt == "json":
        print(json.dumps({"path": args.path, "name": matched.name, "uuid": matched.uuid}, indent=2))
    else:
        print(f"{args.path} [{matched.uuid}]")
    return 0
