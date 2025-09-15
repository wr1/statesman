"""Utilities for config operations."""

import hashlib
import json
from typing import Any, Dict


def sort_dict_recursive(d: Any) -> Any:
    """Recursively sort dictionary keys for consistent hashing."""
    if isinstance(d, dict):
        return {k: sort_dict_recursive(v) for k, v in sorted(d.items())}
    elif isinstance(d, list):
        return [sort_dict_recursive(item) for item in d]
    else:
        return d


def hash_config_section(section: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a config section with sorted keys."""
    sorted_section = sort_dict_recursive(section)
    return hashlib.sha256(json.dumps(sorted_section).encode()).hexdigest()
