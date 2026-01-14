"""Configuration management for AI Employee system."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """Central configuration management using environment variables."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration from environment variables.

        Args:
            env_file: Path to .env file (default: .env in current directory)
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Vault Configuration
        self.vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))

        # Watcher Configuration
        self.watcher_type = os.getenv("WATCHER_TYPE", "filesystem")
        self.watcher_check_interval = int(os.getenv("WATCHER_CHECK_INTERVAL", "60"))

        # Gmail Watcher Configuration
        self.gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH")
        self.gmail_token_path = os.getenv("GMAIL_TOKEN_PATH")
        self.gmail_query = os.getenv("GMAIL_QUERY", "is:unread (urgent OR invoice OR payment)")

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_retention_days = int(os.getenv("LOG_RETENTION_DAYS", "90"))

        # Development Mode
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

        # Performance Settings
        self.max_memory_mb = int(os.getenv("MAX_MEMORY_MB", "50"))

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        # Validate watcher type
        if self.watcher_type not in ["filesystem", "gmail"]:
            raise ConfigurationError(
                f"Invalid WATCHER_TYPE: {self.watcher_type}. "
                "Must be 'filesystem' or 'gmail'"
            )

        # Validate check interval
        if self.watcher_check_interval < 1:
            raise ConfigurationError(
                f"Invalid WATCHER_CHECK_INTERVAL: {self.watcher_check_interval}. "
                "Must be at least 1 second"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid LOG_LEVEL: {self.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )

        # Validate Gmail configuration if using Gmail watcher
        if self.watcher_type == "gmail":
            if not self.gmail_credentials_path:
                raise ConfigurationError(
                    "GMAIL_CREDENTIALS_PATH is required when WATCHER_TYPE is 'gmail'"
                )
            if not self.gmail_token_path:
                raise ConfigurationError(
                    "GMAIL_TOKEN_PATH is required when WATCHER_TYPE is 'gmail'"
                )

    def get_vault_folders(self) -> dict[str, Path]:
        """Get paths to all vault folders."""
        return {
            "inbox": self.vault_path / "Inbox",
            "needs_action": self.vault_path / "Needs_Action",
            "done": self.vault_path / "Done",
            "plans": self.vault_path / "Plans",
            "logs": self.vault_path / "Logs",
            "pending_approval": self.vault_path / "Pending_Approval",
            "approved": self.vault_path / "Approved",
            "rejected": self.vault_path / "Rejected",
        }

    def get_vault_files(self) -> dict[str, Path]:
        """Get paths to core vault files."""
        return {
            "dashboard": self.vault_path / "Dashboard.md",
            "handbook": self.vault_path / "Company_Handbook.md",
            "readme": self.vault_path / "README.md",
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config(vault_path={self.vault_path}, "
            f"watcher_type={self.watcher_type}, "
            f"check_interval={self.watcher_check_interval}s, "
            f"dry_run={self.dry_run})"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """
    Get or create global configuration instance.

    Args:
        env_file: Path to .env file (only used on first call)

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(env_file)
    return _config


def reset_config():
    """Reset global configuration (useful for testing)."""
    global _config
    _config = None
