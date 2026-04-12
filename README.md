# keepassxc-cli

A command-line interface for [KeePassXC](https://keepassxc.org/) that communicates via the browser extension protocol, supporting biometric (TouchID/fingerprint) unlock on supported platforms.

## What it is

`keepassxc-cli` talks to a running KeePassXC instance using the same native messaging protocol used by the KeePassXC Browser extension. This means:

- **Biometric unlock**: On macOS with TouchID (or similar) configured in KeePassXC, you can authenticate via fingerprint rather than typing your master password.
- **No master password in shell history**: Authentication happens through KeePassXC's GUI, not the terminal.
- **Full CRUD**: List, search, add, edit, delete entries and groups.
- **TOTP**: Retrieve time-based one-time passwords.
- **Clipboard**: Copy credentials directly to the clipboard.

## Prerequisites

1. **KeePassXC** ≥ 2.7 with the **Browser Integration** feature enabled:
   - Open KeePassXC → Tools → Settings → Browser Integration
   - Enable "Enable browser integration"
2. A KeePassXC database must be open (or KeePassXC must be running with auto-open configured).
3. Python ≥ 3.10

## Installation

```bash
pipx install keepassxc-cli
```

Or with pip:

```bash
pip install keepassxc-cli
```

## Setup

Before using `keepassxc-cli`, associate it with your KeePassXC instance:

```bash
keepassxc-cli setup
```

This performs a key exchange with KeePassXC (you will be prompted to allow the association in the KeePassXC GUI). The association is saved to `~/.keepassxc/browser-api.json`.

## Usage

### Global options

```
keepassxc-cli [--config PATH] [--browser-api-config PATH] [--format {table,json,tsv}] [-v] COMMAND
```

| Option | Description |
|--------|-------------|
| `--config` | Path to CLI config file (default: `~/.keepassxc/cli.json`) |
| `--browser-api-config` | Path to browser API config file (default: `~/.keepassxc/browser-api.json`) |
| `--format` | Output format: `table` (default), `json`, or `tsv` |
| `-v, --verbose` | Enable verbose/debug logging |

### Commands

#### `setup` — Associate with KeePassXC

```bash
keepassxc-cli setup
```

#### `status` — Connection and association status

```bash
keepassxc-cli status
```

#### `ls` — List entries or groups

```bash
keepassxc-cli ls                # list all entries
keepassxc-cli ls --groups       # list groups (tree view)
keepassxc-cli ls --format json  # output as JSON
```

#### `search` — Search entries

```bash
keepassxc-cli search github
keepassxc-cli search "my bank" --show-password
```

Searches case-insensitively across title, username, and URL fields.

#### `show` — Show entries for a URL

```bash
keepassxc-cli show https://github.com
keepassxc-cli show https://github.com -p   # reveal password
```

#### `add` — Add a new entry

```bash
keepassxc-cli add --url https://example.com --username user@example.com --title "Example"
# Password will be prompted securely if --password is not given
keepassxc-cli add --url https://example.com --username user --password mypass
```

#### `edit` — Edit an entry

```bash
keepassxc-cli edit <uuid> --username newuser
keepassxc-cli edit <uuid> --password newpass --title "New Title"
```

#### `rm` — Delete an entry

```bash
keepassxc-cli rm <uuid>          # prompts for confirmation
keepassxc-cli rm <uuid> --yes    # skip confirmation
```

#### `totp` — Get TOTP code

```bash
keepassxc-cli totp <uuid>
```

#### `clip` — Copy to clipboard

```bash
keepassxc-cli clip https://github.com              # copies password
keepassxc-cli clip https://github.com --field username
keepassxc-cli clip https://github.com --field totp
```

#### `generate` — Generate a password

```bash
keepassxc-cli generate
keepassxc-cli generate --length 32 --symbols
keepassxc-cli generate --no-numbers --no-uppercase
keepassxc-cli generate --clip    # copy to clipboard instead of printing
```

#### `lock` — Lock the database

```bash
keepassxc-cli lock
```

#### `mkdir` — Create a group

```bash
keepassxc-cli mkdir "Work"
keepassxc-cli mkdir "Projects" --parent-uuid <parent-group-uuid>
```

## Configuration

### CLI config (`~/.keepassxc/cli.json`)

Only non-default values are stored. Available options:

| Key | Default | Description |
|-----|---------|-------------|
| `browser_api_config_path` | `~/.keepassxc/browser-api.json` | Path to the browser API config |
| `default_format` | `table` | Default output format (`table`, `json`, `tsv`) |

Example `~/.keepassxc/cli.json`:
```json
{
  "default_format": "json"
}
```

### Browser API config (`~/.keepassxc/browser-api.json`)

Shared with `keepassxc-browser-api`. Contains the association keys created during `keepassxc-cli setup`. This file is automatically created and updated by the `setup` command.

Both config files are stored with `0o600` permissions (owner read/write only).

## Development

```bash
git clone https://github.com/mietzen/keepassxc-cli
cd keepassxc-cli

python3 -m venv .venv
source .venv/bin/activate

# Install local keepassxc-browser-api dependency first
pip install ../mietzen-keepassxc-browser-api/

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest --tb=short -q

# Run linter
ruff check --ignore=E501 --exclude=__init__.py ./keepassxc_cli
```

## Known Limitations

- Requires KeePassXC to be **running** and the database to be **open** (or biometric auto-unlock configured).
- The `clip` and `generate --clip` commands require `pyperclip` and a working clipboard (e.g., `xclip`/`xsel` on Linux, built-in on macOS/Windows).
- The browser integration protocol does not support moving entries between groups directly.
- Entry URLs in the database are stored as `KPH: url` string fields; entries without a URL field may not appear in `show` results.
