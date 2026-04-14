"""Tests for app.config module."""

import os
from pathlib import Path
from unittest import mock

import pytest

from app.config import ENV, settings


def test_env():
    """Test that the ENV constant matches the os.environ variable."""
    assert ENV == os.getenv("ENV", "dev").upper(), f"Expected ENV to be 'dev', but got '{ENV}'"


def test_settings():
    """Test the configuration settings."""
    expected_env = os.getenv("ENV", "dev").upper()

    # check the settings_files list
    expected_settings_file = [
        "config/default.yaml",
        f"config/{expected_env.lower()}.yaml",
        "config/.secrets.yaml",
    ]
    assert settings.settings_file == expected_settings_file, (
        f"Expected settings_files to be {expected_settings_file}, but got {settings.settings_files}"
    )