"""Base class for state management."""

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ValidationError

from statesman.utils.config_utils import hash_config_section


class Statesman:
    """Base class for managing workflow states."""

    def __init__(self, workdir: str, config_path: str):
        self.workdir = Path(workdir).resolve()
        self.config_path = Path(config_path).resolve()
        self.config = self.load_config()
        self.state_file = self.workdir / ".statesman_state.yaml"
        self.previous_states = self.load_previous_states()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def load_previous_states(self) -> Dict[str, str]:
        """Load previous state hashes from file."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_state(self, section: str, hash_value: str):
        """Save state hash for a section."""
        self.previous_states[section] = hash_value
        with open(self.state_file, "w") as f:
            yaml.safe_dump(self.previous_states, f)

    def has_section_changed(self, section: str) -> bool:
        """Check if a config section has changed."""
        current_hash = hash_config_section(self.config.get(section, {}))
        previous_hash = self.previous_states.get(section)
        return current_hash != previous_hash

    def validate_state(self, model: BaseModel):
        """Validate a Pydantic state model."""
        try:
            model.model_validate(model)
        except ValidationError as e:
            raise ValueError(f"State validation failed: {e}") from e
