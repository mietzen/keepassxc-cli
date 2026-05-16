# keepassxc-cli - Claude Code Instructions

## Project Overview

`keepassxc-cli` is a Python command-line tool that communicates with a running KeePassXC instance using the KeePassXC Browser Extension protocol (native messaging over a Unix socket). It enables terminal users to interact with KeePassXC — adding, editing, and deleting entries — while leveraging KeePassXC's biometric (TouchID/fingerprint) unlock support.

## Architecture

### Package Structure

```
keepassxc_cli/
├── __init__.py          # empty (just from __future__ import annotations)
├── __main__.py          # CLI entry point; argument parsing; dispatches to commands
├── config.py            # CliConfig dataclass; save/load ~/.keepassxc/cli.json
├── output.py            # Output formatting: table, json; ensure_scheme() URL helper
└── commands/
    ├── __init__.py      # empty
    ├── setup.py         # associate with KeePassXC
    ├── status.py        # show connection/association status
    ├── show.py          # show entries by URL
    ├── add.py           # add new entry: positional url/username, --group/--group-uuid optional
    ├── edit.py          # edit existing entry: positional url, --uuid/--username/--password optional
    ├── rm.py            # delete entry: positional url, --uuid optional for disambiguation
    ├── totp.py          # get TOTP code
    ├── clip.py          # copy field to clipboard: positional url then field
    ├── lock.py          # lock database
    ├── mkdir.py         # create group
    ├── group_uuid.py    # look up a group UUID by path
    └── version.py       # print installed package version

tests/
├── conftest.py          # fixtures: mock_entry, mock_group, mock_browser_config, mock_client
├── test_config.py       # CliConfig unit tests
├── test_output.py       # output formatting tests
└── test_commands.py     # command run() function tests with mocked BrowserClient
```

### Dependencies

This package depends on `keepassxc-browser-api` (local package at `../mietzen-keepassxc-browser-api/`), which provides:

- `BrowserClient` — the main client that communicates with KeePassXC
- `BrowserConfig` — configuration dataclass (associations, keys)
- `Entry`, `Group` — data models
- Exceptions: `KeePassXCError`, `AssociationError`, `NotAssociatedError`, `DatabaseLockedError`, `ProtocolError`, `ConnectionError`

Import path: `from keepassxc_browser_api import BrowserClient, BrowserConfig, Entry, Group`

## Command Module Convention

Every command module (`keepassxc_cli/commands/*.py`) must implement:

```python
def add_parser(subparsers) -> None:
    p = subparsers.add_parser("name", help="...")
    # add arguments
    p.set_defaults(func=run)

def run(client, args, cli_config, browser_config, browser_config_path, *, fmt="table") -> int:
    # returns 0 on success, non-zero on failure
    ...
```

The `run()` function signature is always:
```python
def run(
    client: BrowserClient,
    args: argparse.Namespace,
    cli_config: CliConfig,
    browser_config: BrowserConfig,
    browser_config_path: Path,
    *,
    fmt: str = "table",
) -> int:
```

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ../mietzen-keepassxc-browser-api/   # local dependency
pip install -e ".[dev]"

# Run tests
pytest --tb=short -q

# Run tests with coverage
pytest --cov=keepassxc_cli --cov-report=term-missing

# Lint
ruff check --ignore=E501 --exclude=__init__.py ./keepassxc_cli
```

## Conventions

- **`from __future__ import annotations`** must be the first line of every `.py` source file.
- **Ruff**: `ruff check --ignore=E501 --exclude=__init__.py ./keepassxc_cli`
- **No async code**: Everything is synchronous. No threads in the CLI.
- **Output**: Use `print()` for normal (stdout) output. Error/warning messages use `logger.error()` / `logger.warning()` — never `print(file=sys.stderr)` directly.
- **Logging config**: Set by `__main__.py`. Non-verbose: `WARNING` level, `"%(message)s"` format, to `sys.stderr`. Verbose (`-v`): `DEBUG` level with timestamp format to `sys.stderr`.
- **Exit codes**: `run()` functions return `int` (0 = success, non-zero = failure). `__main__.py` maps exceptions to exit codes:

  | Code | Meaning |
  |---|---|
  | `0` | Success |
  | `1` | Generic error (`KeePassXCError`, `OSError`, `JSONDecodeError`, unknown `ProtocolError`) |
  | `2` | `ConnectionError` — KeePassXC not running / socket not found |
  | `3` | `DatabaseLockedError` — unlock timeout exceeded |
  | `4` | `ProtocolError(error_code=6 or 19)` — access denied by user |

- **Config permissions**: Config files are written with `0o600` (owner read/write only).
- **URL normalisation**: All URL-accepting command `run()` functions call `ensure_scheme(url)` (from `output.py`) before passing the URL to any `BrowserClient` method. This auto-prepends `https://` for bare hostnames (e.g. `example.com`) and emits a `logger.warning`. KeePassXC derives the entry title from `QUrl(url).host()`, which returns `""` for URLs without a scheme.
- **Venv**: Always use `.venv` for development.
- **Python ≥ 3.10** required.
- **Password visibility**: `show` omits password and TOTP entirely when `-p` is not passed (no masking).

## Config Files

| File | Purpose |
|------|---------|
| `~/.keepassxc/cli.json` | CLI preferences (default format, custom browser-api config path). Only non-default values stored. |
| `~/.keepassxc/browser-api.json` | Shared with keepassxc-browser-api. Contains association keys. Written by `setup` command. |

## Output Formats

Two formats are supported: `table` (default) and `json`. The `-j / --json` flag on individual subcommands or `default_format` in `cli.json` controls the default.

## CI

- `lint_and_test.yml` — Unit tests + ruff lint across Python 3.10–3.14
- `pypi.yml` — Build & publish on release, then dispatch to homebrew-tap to update the formula
- `auto-release.yml` — Auto-create patch release on dependabot merge
- `auto-merge-dependabot.yml` — Auto-merge dependabot PRs
