"""Creational - Singleton: the config file is read once and shared by every module."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).with_name("config.json")


class ConfigManager:
    """Always obtained through get_instance(), never with ConfigManager() directly."""

    _instance: ConfigManager | None = None

    def __init__(self, path: Path | str) -> None:
        with open(path, encoding="utf-8") as f:
            self._data = json.load(f)

    @classmethod
    def get_instance(cls, path: Path | str = CONFIG_FILE) -> ConfigManager:
        if cls._instance is None:
            cls._instance = cls(path)  # the only file read
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Forget the instance. Only the tests need this."""
        cls._instance = None

    def get(self, key: str, default=None):
        """Dotted access to nested values: get("database.host")."""
        value = self._data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set(self, key: str, value) -> None:
        """Change a value; every module sees it since they share the instance."""
        *parents, last = key.split(".")
        node = self._data
        for part in parents:
            node = node.setdefault(part, {})
        node[last] = value


# The four "modules" of the exercise, now without load_config()
def start_application() -> str:
    config = ConfigManager.get_instance()
    return f"Starting {config.get('app.name')} (debug={config.get('app.debug')})"


def connect_database() -> str:
    config = ConfigManager.get_instance()
    return f"Connecting to database at {config.get('database.host')}:{config.get('database.port')}"


def send_email(to: str, subject: str) -> str:
    config = ConfigManager.get_instance()
    return (f"Sending '{subject}' to {to} from {config.get('email.sender')} "
            f"via {config.get('email.smtp_host')}")


def process_payment(amount: float) -> str:
    config = ConfigManager.get_instance()
    return f"Processing {amount}€ in {config.get('payment.environment')} mode"


if __name__ == "__main__":
    print(start_application())
    print(connect_database())
    print(send_email("user@test.com", "Welcome"))
    print(process_payment(99.99))
