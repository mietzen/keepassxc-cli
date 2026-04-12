from __future__ import annotations

import argparse
import sys
from pathlib import Path

from keepassxc_browser_api import BrowserClient, BrowserConfig

from keepassxc_cli.config import CliConfig
from keepassxc_cli.output import print_password


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate", help="Generate a password")
    p.add_argument("--length", type=int, default=20, help="Password length (default: 20)")
    p.add_argument("--no-numbers", action="store_true", help="Exclude numbers")
    p.add_argument("--no-lowercase", action="store_true", help="Exclude lowercase letters")
    p.add_argument("--no-uppercase", action="store_true", help="Exclude uppercase letters")
    p.add_argument("--symbols", action="store_true", help="Include symbols")
    p.add_argument("--special", action="store_true", help="Include special characters")
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
    password = client.generate_password(
        length=args.length,
        numbers=not args.no_numbers,
        lowercase=not args.no_lowercase,
        uppercase=not args.no_uppercase,
        symbols=args.symbols,
        special=args.special,
    )
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
