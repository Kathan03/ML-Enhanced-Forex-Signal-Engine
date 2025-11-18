"""
Configuration management for the forex signal engine.

This module handles:
- Loading YAML configuration files
- Environment variable substitution
- Configuration validation
- Default values
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv


class ConfigLoader:
    """
    Loads and manages configuration from YAML files.

    Supports:
    - Environment variable substitution (${VAR_NAME})
    - Nested configuration access
    - Default values
    - Validation

    Example:
        >>> config = ConfigLoader("config.yaml")
        >>> symbol = config.get("data.symbol")
        >>> api_key = config.get("data.api_key")  # Reads from env var
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}

        # Load environment variables
        load_dotenv()

        # Load configuration
        self.load()

    def load(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Substitute environment variables
        self.config = self._substitute_env_vars(self.config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., "data.symbol")
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get("data.symbol")  # "EURUSD"
            >>> config.get("data.api_key")
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key.

        Args:
            key: Dot-separated key
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config.

        Replaces ${VAR_NAME} with os.environ.get("VAR_NAME")

        Args:
            config: Configuration dict or value

        Returns:
            Configuration with substituted values
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.environ.get(env_var, config)
        else:
            return config

    def validate(self) -> bool:
        """
        Validate configuration has required fields.

        Returns:
            True if valid

        Raises:
            ValueError: If required fields missing
        """
        required_fields = [
            "data.symbol",
            "data.timeframe",
            "model.type",
            "signals.thresholds.buy_probability",
            "signals.thresholds.sell_probability"
        ]

        for field in required_fields:
            if self.get(field) is None:
                raise ValueError(f"Required configuration field missing: {field}")

        return True

    def to_dict(self) -> Dict:
        """
        Get full configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config
