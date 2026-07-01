"""Configuration management for Armarius.

Handles reading/writing ~/.armarius/config.yaml and environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional

import yaml


class ArmariusConfig:
    """Armarius configuration manager."""

    DEFAULT_CONFIG_DIR = Path.home() / ".armarius"
    DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
    DEFAULT_LOG_DIR = DEFAULT_CONFIG_DIR / "logs"

    @classmethod
    def build_default_config(cls) -> dict:
        """Build default config from current class paths.

        Using a method instead of a class-level frozen dict keeps tests and
        monkeypatched paths aligned with the active config directory.
        """
        return {
            "library": {
                "root_path": str(Path.home() / "Documents" / "papers"),
                "recursive_scan": True,
                "default_path": None,
            },
            "database": {
                "path": str(cls.DEFAULT_CONFIG_DIR / "armarius.db"),
            },
            "web": {
                "host": "localhost",
                "port": 8501,
                "auto_open_browser": True,
            },
            "i18n": {
                "locale": "zh-TW",
            },
            "theme": {
                "mode": "light",
            },
            "logging": {
                "level": "INFO",
                "path": str(cls.DEFAULT_LOG_DIR / "armarius.log"),
            },
        }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_path: Path to config file. Defaults to ~/.armarius/config.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file or create default.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return self.build_default_config().copy()

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Merge with defaults (in case new keys were added)
        return self._merge_configs(self.build_default_config(), config)

    def _merge_configs(self, default: dict, user: dict) -> dict:
        """Recursively merge user config with defaults.

        Args:
            default: Default configuration
            user: User configuration

        Returns:
            Merged configuration
        """
        result = default.copy()
        for key, value in user.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def save(self) -> None:
        """Save configuration to file."""
        # Create config directory if not exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create log directory if specified
        log_path = Path(self.config["logging"]["path"])
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path.

        Args:
            key_path: Dot-separated key path (e.g., "library.root_path")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("library.root_path")
            "/Users/justyn/Documents/papers"
        """
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value) -> None:
        """Set configuration value by dot-separated path.

        Args:
            key_path: Dot-separated key path (e.g., "library.root_path")
            value: Value to set

        Example:
            >>> config.set("library.root_path", "/path/to/papers")
        """
        keys = key_path.split(".")
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    @property
    def library_root(self) -> Path:
        """Get library root path with environment variable override.

        Returns:
            Library root path

        Environment:
            ARMARIUS_LIBRARY_ROOT: Override config value
        """
        env_override = os.getenv("ARMARIUS_LIBRARY_ROOT")
        if env_override:
            return Path(env_override).expanduser()
        
        # Use default_path if set, otherwise use root_path
        default_path = self.get("library.default_path")
        if default_path:
            return Path(default_path).expanduser()
        
        return Path(self.get("library.root_path")).expanduser()

    @property
    def web_port(self) -> int:
        """Get web UI port with environment variable override.

        Returns:
            Web UI port

        Environment:
            ARMARIUS_WEB_PORT: Override config value
        """
        env_override = os.getenv("ARMARIUS_WEB_PORT")
        if env_override:
            return int(env_override)
        return int(self.get("web.port", 8501))

    @property
    def recursive_scan(self) -> bool:
        """Get recursive scan setting.

        Returns:
            True if recursive scan enabled
        """
        return bool(self.get("library.recursive_scan", True))

    @property
    def locale(self) -> str:
        """Get the active UI locale.

        Returns:
            Locale code stored in config.
        """
        return str(self.get("i18n.locale", "zh-TW"))

    @property
    def theme_mode(self) -> str:
        """Get the preferred theme mode.

        Returns:
            Theme mode: ``light``, ``dark``, or ``auto``.
        """
        return str(self.get("theme.mode", "light"))
