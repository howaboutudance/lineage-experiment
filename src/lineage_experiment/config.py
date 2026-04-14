"""Configuration and setup for lineage-experiment."""

import logging
import os

import dynaconf

# logger
_log = logging.getLogger(__name__)

# Applicationg environment:
# - dev -- development
# - test -- testing
# - prod -- production
ENV = os.getenv("ENV", "dev").upper()

# Configuration settings
# load setting from default and layer with environment specific settings
# and secrets (if present)
settings = dynaconf.Dynaconf(
    settings_files=["config/default.yaml", f"config/{ENV.lower()}.yaml", "config/.secrets.yaml"],
    load_dotenv=True,
)
