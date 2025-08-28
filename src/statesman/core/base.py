"""Base class for state management."""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from pydantic import BaseModel, ValidationError

from statesman.utils.config_utils import hash_config_section

from statesman.models.state import FileState


class ManagedFile(BaseModel):
    """Configuration for a managed file."""

    name: str
    non_empty: bool = True
    newer_than: Union[str, Path, None] = None  # Can be 'config' or a Path


class Statesman:
    """Base class for managing workflow states."""

    input_files: List[ManagedFile] = []
    output_files: List[str] = []
    dependent_sections: List[str] = []

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
            model.model_validate(model.dict())
        except ValidationError as e:
            raise ValueError(f"State validation failed: {e}") from e

    def needs_run(self) -> bool:
        """Determine if the step needs to be run based on inputs, outputs, and sections."""
        # Check inputs
        for mf in self.input_files:
            path = self.workdir / mf.name
            newer_than = self.config_path if mf.newer_than == 'config' else mf.newer_than
            state = FileState(path=path, non_empty=mf.non_empty, newer_than=newer_than)
            try:
                self.validate_state(state)
            except ValueError:
                return True  # Needs run if validation fails

        # Check if any output is missing
        for out_name in self.output_files:
            out_path = self.workdir / out_name
            if not out_path.exists() or not out_path.stat().st_size > 0:
                return True

        # Check if any dependent section changed
        for section in self.dependent_sections:
            if self.has_section_changed(section):
                return True

        return False

    def run(self):
        """Run the step if necessary and update states."""
        if self.needs_run():
            self._execute()
            # Update states for dependent sections
            for section in self.dependent_sections:
                current_hash = hash_config_section(self.config.get(section, {}))
                self.save_state(section, current_hash)
            # Optionally, validate outputs after execution
            for out_name in self.output_files:
                out_path = self.workdir / out_name
                if not out_path.exists() or not out_path.stat().st_size > 0:
                    raise RuntimeError(f"Output file {out_name} was not created properly.")

    def _execute(self):
        """User-defined execution logic. Subclasses should override this."""
        raise NotImplementedError("Subclasses must implement _execute method.")
