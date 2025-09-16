"""Utilities for config operations."""

import hashlib
from io import StringIO
from typing import Any, Dict

import ruamel.yaml as yaml


def sort_dict_recursive(d: Any) -> Any:
    """Recursively sort dictionary keys and round floats for consistent hashing."""
    if isinstance(d, dict):
        for k in d.keys():
            if isinstance(k, float):
                raise ValueError(
                    "Float keys are deprecated and not supported in config sections."
                )
        new_d = {}
        for k, v in d.items():
            k = str(k)
            new_d[k] = sort_dict_recursive(v)
        return {k: sort_dict_recursive(v) for k, v in sorted(new_d.items())}
    elif isinstance(d, list):
        return [sort_dict_recursive(item) for item in d]
    else:
        if isinstance(d, float):
            return round(d, 10)
        return d


def hash_config_section(section: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a config section using ruamel.yaml for consistent string representation."""
    # Sort the section recursively
    sorted_section = sort_dict_recursive(section)
    # Dump to YAML string with sorted keys for consistency
    stream = StringIO()
    y = yaml.YAML()
    y.dump(sorted_section, stream)
    yaml_str = stream.getvalue()
    return hashlib.sha256(yaml_str.encode()).hexdigest()
