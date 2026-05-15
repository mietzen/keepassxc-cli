# keepassxc-cli

A command-line interface for [KeePassXC](https://keepassxc.org/) that communicates via the browser extension protocol, supporting biometric (TouchID/fingerprint) unlock on supported platforms.

## What it is

`keepassxc-cli` talks to a running KeePassXC instance using the same native messaging protocol used by the KeePassXC Browser extension. This means:

- **Biometric unlock**: On macOS with TouchID (or similar) configured in KeePassXC, you can authenticate via fingerprint rather than typing your master password.
- **No master password in shell history**: Authentication happens through KeePassXC's GUI, not the terminal.
- **CRUD**: Add, edit, delete entries and groups.
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
keepassxc-cli [--config PATH] [--browser-api-config PATH] [-v] COMMAND [COMMAND OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--config` | Path to CLI config file (default: `~/.keepassxc/cli.json`) |
| `--browser-api-config` | Path to browser API config file (default: `~/.keepassxc/browser-api.json`) |
| `-v, --verbose` | Enable verbose/debug logging |

Some commands support a `-j / --json` flag for JSON output — pass it anywhere after the subcommand name:

```bash
keepassxc-cli show https://github.com -j
keepassxc-cli status -j
```

### Commands

#### `setup` — Associate with KeePassXC

```bash
keepassxc-cli setup
```

#### `status` — Connection and association status

```bash
keepassxc-cli status
keepassxc-cli status -j
```

#### `show` — Show entries for a URL

```bash
keepassxc-cli show https://github.com
keepassxc-cli show https://github.com -p     # reveal password and TOTP
keepassxc-cli show https://github.com -j
```

Without `-p`, password and TOTP are omitted from the output entirely.

#### `totp` — Get TOTP code

```bash
keepassxc-cli totp https://github.com
keepassxc-cli totp https://github.com -j
```

#### `clip` — Copy a field to clipboard

```bash
keepassxc-cli clip password https://github.com
keepassxc-cli clip username https://github.com
keepassxc-cli clip totp     https://github.com
```

#### `add` — Add a new entry

```bash
# Password is prompted securely if --password is not given
keepassxc-cli add --url https://example.com --username user@example.com
keepassxc-cli add --url https://example.com --username user --password mypass
# Place the entry in a specific group by UUID
keepassxc-cli add --url https://example.com --username user --group-uuid <group-uuid>
```

> **Note**: The entry title is always derived from the URL hostname by KeePassXC. The protocol has no field to set a custom title.

#### `edit` — Edit an entry

```bash
# Get the UUID first
keepassxc-cli show https://github.com -p

# Then edit — --url is required to resolve the current entry
keepassxc-cli edit <uuid> --url https://github.com --username newuser
keepassxc-cli edit <uuid> --url https://github.com --password newpass --title "New Title"
```

#### `rm` — Delete an entry

```bash
keepassxc-cli rm <uuid>        # prompts for confirmation
keepassxc-cli rm <uuid> --yes  # skip confirmation
```

#### `lock` — Lock the database

```bash
keepassxc-cli lock
```

#### `mkdir` — Create a group

```bash
keepassxc-cli mkdir "Work"
keepassxc-cli mkdir "Work/Projects"   # create Projects inside Work
```

Use `/`-separated paths to create nested groups. KeePassXC creates any missing path segments automatically.

#### `group-uuid` — Look up a group's UUID by path

```bash
keepassxc-cli group-uuid "Work"
keepassxc-cli group-uuid "Work/Projects"
keepassxc-cli group-uuid "Work/Projects" -j
```

Returns the UUID for the group at the given path (relative to the database root). Useful for scripting — pipe the UUID into `add --group-uuid`.

JSON output (`-j`):
```json
{
  "path": "Work/Projects",
  "name": "Projects",
  "uuid": "<uuid>"
}
```

#### `version` — Show the CLI version

```bash
keepassxc-cli version
```

Does not require a running KeePassXC instance.

## Configuration

### CLI config (`~/.keepassxc/cli.json`)

Only non-default values are stored. Available options:

| Key | Default | Description |
|-----|---------|-------------|
| `browser_api_config_path` | `~/.keepassxc/browser-api.json` | Path to the browser API config |
| `default_format` | `table` | Default output format (`table` or `json`) |

Example `~/.keepassxc/cli.json`:
```json
{
  "default_format": "json"
}
```

### Browser API config (`~/.keepassxc/browser-api.json`)

Shared with `keepassxc-browser-api`. Contains the association keys created during `keepassxc-cli setup`. This file is automatically created and updated by the `setup` command.

Both config files are stored with `0o600` permissions (owner read/write only).

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Generic error (unexpected KeePassXC error, OS error, config parse error) |
| `2` | KeePassXC is not running or the socket is not found (`ConnectionError`) |
| `3` | Database unlock timed out (`DatabaseLockedError`) |
| `4` | Access denied by user — either the access prompt was cancelled or "Allow access to all entries" was denied |

These codes are stable and suitable for scripting, e.g.:

```bash
keepassxc-cli show https://example.com || case $? in
  2) echo "Start KeePassXC first" ;;
  3) echo "Unlock timed out" ;;
  4) echo "Access denied" ;;
esac
```

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
- The `clip` command requires `pyperclip` and a working clipboard (e.g., `xclip`/`xsel` on Linux, built-in on macOS/Windows).
- The browser integration protocol does not support moving entries between groups directly.
- Entry lookup is by URL/hostname only (same as the browser extension). Title-based search is not supported by the protocol.
- **String fields** (`string_fields` in JSON output) require the KeePassXC setting "Support KPH fields" to be enabled, and custom attributes must be prefixed with `KPH: ` in the KeePassXC entry's "Advanced" tab. This is a server-side KeePassXC requirement, not something the CLI can control.
