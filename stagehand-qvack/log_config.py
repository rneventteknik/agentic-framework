import logging
import os


def log_level_from_env() -> int:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if not isinstance(level, int):
        return logging.INFO
    return level


def configure_logging() -> None:
    logging.basicConfig(level=log_level_from_env())
