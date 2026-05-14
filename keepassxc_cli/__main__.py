"""CLI entry point for keepassxc-cli."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig
from keepassxc_browser_api.exceptions import KeePassXCError, ConnectionError

from .config import CliConfig, DEFAULT_CLI_CONFIG_PATH
from .commands import setup, status, show, add, edit, rm, totp, clip, lock, mkdir, group_uuid, version

# Shared parent parser that injects -j/--json into each subparser that supports it.
# Defined at module level so command modules can import it if needed.
fmt_parent = argparse.ArgumentParser(add_help=False)
fmt_parent.add_argument(
    "-j", "--json",
    action="store_true",
    dest="json_output",
    default=False,
    help="Output as JSON",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="keepassxc-cli",
        description="CLI for KeePassXC using the browser extension protocol with biometric unlock",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CLI_CONFIG_PATH),
        help="Path to CLI config file (default: %(default)s)",
    )
    parser.add_argument(
        "--browser-api-config",
        default=None,
        help="Path to browser API config file",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    setup.add_parser(subparsers)
    status.add_parser(subparsers, fmt_parent)
    show.add_parser(subparsers, fmt_parent)
    add.add_parser(subparsers)
    edit.add_parser(subparsers)
    rm.add_parser(subparsers)
    totp.add_parser(subparsers, fmt_parent)
    clip.add_parser(subparsers)
    lock.add_parser(subparsers)
    mkdir.add_parser(subparsers)
    group_uuid.add_parser(subparsers, fmt_parent)
    version.add_parser(subparsers)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    cli_config_path = Path(args.config)
    cli_config = CliConfig.load(cli_config_path)

    browser_api_config_path = Path(args.browser_api_config or cli_config.browser_api_config_path)
    browser_config = BrowserConfig.load(browser_api_config_path)

    fmt = "json" if getattr(args, "json_output", False) else cli_config.default_format

    client = BrowserClient(browser_config)
    try:
        rc = args.func(client, args, cli_config, browser_config, browser_api_config_path, fmt=fmt)
    except (KeePassXCError, ConnectionError, OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        rc = 1
    sys.exit(rc)
