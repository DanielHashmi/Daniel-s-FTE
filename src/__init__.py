"""AI Employee - Bronze Tier Foundation Package."""

__version__ = "0.1.0"
__author__ = "Daniel Hashmi"

from .config import get_config, Config
from .watchers import BaseWatcher

__all__ = ["get_config", "Config", "BaseWatcher"]
