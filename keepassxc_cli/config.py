from __future__ import annotations

import json
import logging
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BROWSER_API_CONFIG_PATH = str(Path.home() / ".keepassxc" / "browser-api.json")
DEFAULT_CLI_CONFIG_PATH = Path.home() / ".keepassxc" / "cli.json"

logger = logging.getLogger(__name__)


@dataclass
class CliConfig:
    browser_api_config_path: str = field(default_factory=lambda: DEFAULT_BROWSER_API_CONFIG_PATH)
    default_format: str = "table"

    def to_dict(self) -> dict:
        d: dict = {}
        if self.browser_api_config_path != DEFAULT_BROWSER_API_CONFIG_PATH:
            d["browser_api_config_path"] = self.browser_api_config_path
        if self.default_format != "table":
            d["default_format"] = self.default_format
        return d

    @classmethod
    def from_dict(cls, d: dict) -> CliConfig:
        return cls(
            browser_api_config_path=d.get("browser_api_config_path", DEFAULT_BROWSER_API_CONFIG_PATH),
            default_format=d.get("default_format", "table"),
        )

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(str(path.parent), stat.S_IRWXU)
        data = json.dumps(self.to_dict(), indent=2)
        # Write with restricted permissions (0o600)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, data.encode())
        finally:
            os.close(fd)

    @classmethod
    def load(cls, path: Path | str) -> CliConfig:
        path = Path(path)
        if not path.exists():
            return cls()
        mode = path.stat().st_mode
        if mode & 0o077:
            logger.warning(
                "Config file %s has insecure permissions %o; expected 0600. "
                "Fix with: chmod 600 %s",
                path, mode & 0o777, path,
            )
        with open(path) as f:
            d = json.load(f)
        return cls.from_dict(d)
