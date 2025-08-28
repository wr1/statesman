"""Utilities for config operations."""

import hashlib
import json
from typing import Any, Dict


def hash_config_section(section: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a config section."""
    return hashlib.sha256(json.dumps(section, sort_keys=True).encode()).hexdigest()
