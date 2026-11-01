import logging

from log_config import log_level_from_env


def test_log_level_from_env_defaults_to_info(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert log_level_from_env() == logging.INFO


def test_log_level_from_env_honors_log_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    assert log_level_from_env() == logging.WARNING


def test_log_level_from_env_falls_back_for_invalid_value(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "not-a-level")
    assert log_level_from_env() == logging.INFO
