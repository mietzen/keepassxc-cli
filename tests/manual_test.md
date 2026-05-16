
## Manual Test Plan

These tests require KeePassXC to be running with a database open and browser integration enabled. Run `keepassxc-cli setup` once before starting.

### Prerequisites

```bash
keepassxc-cli setup          # allow association in the KeePassXC popup
keepassxc-cli status         # should print "Connected" and association info
keepassxc-cli status -j      # same, JSON output
keepassxc-cli version        # prints version, no KeePassXC required
keepassxc-cli version -j     # {"version": "<semver>"}
```

---

### `mkdir` — Create groups

```bash
# Create a top-level group
keepassxc-cli mkdir "TestGroup"
# Expected: "Group created." + name/uuid

# Create a nested group (parent must exist)
keepassxc-cli mkdir "TestGroup/Sub"
# Expected: "Group created." with path TestGroup/Sub

# JSON output
keepassxc-cli mkdir "TestGroup/Sub2" -j
# Expected: {"name": "Sub2", "uuid": "<uuid>"}
```

---

### `group-uuid` — Look up group UUID

```bash
keepassxc-cli group-uuid "TestGroup"
# Expected: prints UUID of TestGroup

keepassxc-cli group-uuid "TestGroup/Sub" -j
# Expected: {"path": "TestGroup/Sub", "name": "Sub", "uuid": "<uuid>"}

keepassxc-cli group-uuid "DoesNotExist"
# Expected: non-zero exit code, error message
```

---

### `add` — Add entries

```bash
# Minimal: positional url + username, password prompted
keepassxc-cli add https://test.example.com alice
# Expected: prompts for password twice, prints "Entry added.", entry visible in KeePassXC

# Password inline
keepassxc-cli add https://test2.example.com bob --password s3cr3t
# Expected: "Entry added." without password prompt

# Into a specific group by path
keepassxc-cli add https://test3.example.com carol --password pass --group "TestGroup"
# Expected: "Entry added.", entry under TestGroup in KeePassXC

# Into a specific group by UUID (use UUID from group-uuid above)
keepassxc-cli add https://test4.example.com dave --password pass --group-uuid <uuid-from-group-uuid>
# Expected: "Entry added.", entry under TestGroup in KeePassXC

# JSON output
keepassxc-cli add https://test5.example.com eve --password pass -j
# Expected: {"status": "ok", "message": "Entry added."}

# Bare hostname (no scheme) — should auto-prefix https:// with warning
keepassxc-cli add noscheme.example.com frank --password pass
# Expected: warning on stderr "Prefixing https://", "Entry added."

# Duplicate: adding same URL+username again
keepassxc-cli add https://test.example.com alice --password s3cr3t
# Expected: create a second entry (KeePassXC allows duplicates)
```

---

### `show` — Show entries

```bash
keepassxc-cli show https://test.example.com
# Expected: table with username, URL; password/TOTP hidden

keepassxc-cli show https://test.example.com -p
# Expected: same table with password column revealed

keepassxc-cli show https://test.example.com -j
# Expected: JSON array of entries, password field absent

keepassxc-cli show https://test.example.com -p -j
# Expected: JSON with password included

keepassxc-cli show https://doesnotexist.example.com
# Expected: "No entries found" message, exit code 1
```

---

### `totp` — Get TOTP code

> Requires an entry with TOTP configured in KeePassXC.

```bash
keepassxc-cli totp https://github.com
# Expected: 6-digit TOTP code

keepassxc-cli totp https://github.com -j
# Expected: {"totp": "<code>"}

keepassxc-cli totp https://test.example.com     # entry without TOTP
# Expected: error or empty, non-zero exit
```

---

### `clip` — Copy field to clipboard

```bash
# URL is first positional arg, field is second
keepassxc-cli clip https://test.example.com password
# Expected: "Copied password to clipboard.", clipboard contains password

keepassxc-cli clip https://test.example.com username
# Expected: "Copied username to clipboard."

keepassxc-cli clip https://github.com totp
# Expected: copies current TOTP code

# Invalid field name
keepassxc-cli clip https://test.example.com nosuchfield
# Expected: error, non-zero exit
```

---

### `edit` — Edit entries

```bash
# Edit username (URL matches single entry)
keepassxc-cli edit https://test2.example.com --username newbob
# Expected: "Entry updated.", verify new username in KeePassXC

# Edit password
keepassxc-cli edit https://test2.example.com --password newpass
# Expected: "Entry updated."

# URL matches multiple entries — must provide --uuid
keepassxc-cli edit https://test.example.com --username updated
# Expected: error listing multiple matches, prompts for --uuid

keepassxc-cli edit https://test.example.com --uuid <uuid> --username updated
# Expected: "Entry updated."

# JSON output
keepassxc-cli edit https://test2.example.com --username finalbob -j
# Expected: {"status": "ok", "message": "Entry updated."}

# Non-existent URL
keepassxc-cli edit https://ghost.example.com --username x
# Expected: error, non-zero exit
```

---

### `rm` — Delete entries

```bash
# Single match — prompts for confirmation
keepassxc-cli rm https://test2.example.com
# Expected: confirmation prompt; enter 'y' → "Entry deleted."

# Skip confirmation
keepassxc-cli rm https://test3.example.com --yes
# Expected: "Entry deleted." without prompt

# JSON output
keepassxc-cli rm https://test4.example.com --yes -j
# Expected: {"status": "ok", "message": "Entry deleted."}

# Multiple matches — must provide --uuid
keepassxc-cli rm https://test.example.com --yes
# Expected: error table listing all matches, asks to rerun with --uuid

keepassxc-cli rm https://test.example.com --uuid <uuid> --yes
# Expected: "Entry deleted.", only that entry removed

# Non-existent URL
keepassxc-cli rm https://gone.example.com --yes
# Expected: error, non-zero exit
```

---

### `lock` — Lock the database

```bash
keepassxc-cli lock
# Expected: "Database locked.", KeePassXC GUI shows locked state

keepassxc-cli lock -j
# Expected: {"status": "ok", "message": "Database locked."}

# After locking — subsequent commands should trigger unlock or fail
keepassxc-cli status
# Expected: "Database locked" or unlock prompt depending on biometric config
```

---

### `unlock` — Unlock the database

```bash
# First lock the database
keepassxc-cli lock

# Then unlock (triggers TouchID/biometrics if configured)
keepassxc-cli unlock
# Expected: "Database unlocked.", KeePassXC GUI shows unlocked state

keepassxc-cli lock && keepassxc-cli unlock -j
# Expected: {"status": "ok", "message": "Database unlocked."}

# Quit KeePassXC entirely, then:
keepassxc-cli unlock
# Expected: error "Cannot connect to KeePassXC", exit code 2
```
