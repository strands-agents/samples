"""Configuration management for different environments."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_log_level() -> str:
    """Get the configured log level."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_output_directory() -> str:
    """Get the directory for output files."""
    return os.getenv("OUTPUT_DIR", "./output")


def ensure_output_directory() -> str:
    """Ensure output directory exists and return path."""
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
