from __future__ import annotations

import argparse
import logging
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import ensure_scheme, print_entry_detail

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser("show", parents=parents, help="Show entries matching a URL")
    p.add_argument("url", help="URL or search string")
    p.add_argument("-p", "--show-password", action="store_true", help="Reveal password and TOTP")
    p.add_argument("--show-kph-prefix", action="store_true", help="Keep 'KPH: ' prefix on custom string field names")
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
    url = ensure_scheme(args.url)
    entries = client.get_logins(url)
    if not entries:
        logger.warning("No entries found for: %s", url)
        return 1
    for entry in entries:
        print_entry_detail(entry, fmt, show_password=args.show_password, show_kph_prefix=getattr(args, "show_kph_prefix", False))
        if fmt == "table" and len(entries) > 1:
            print()
    return 0
