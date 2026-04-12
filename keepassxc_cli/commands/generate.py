from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_password


def add_parser(subparsers: argparse._SubParsersAction, fmt_parent: argparse.ArgumentParser | None = None) -> None:
    parents = [fmt_parent] if fmt_parent else []
    p = subparsers.add_parser(
        "generate",
        parents=parents,
        help="Generate a password using KeePassXC's configured password profile",
    )
    p.add_argument("--clip", action="store_true", help="Copy to clipboard instead of printing")
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
    password = client.generate_password()
    if password is None:
        print("Failed to generate password.", file=sys.stderr)
        return 1

    if args.clip:
        try:
            import pyperclip
            pyperclip.copy(password)
            print("Password copied to clipboard.")
        except ImportError:
            print("Error: pyperclip is required for clipboard support. Install it with: pip install pyperclip", file=sys.stderr)
            return 1
    else:
        print_password(password, fmt)

    return 0
