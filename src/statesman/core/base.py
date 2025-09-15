"""Base class for state management."""

from pathlib import Path
from typing import Any, Dict, List, Union

import logging
import yaml
from pydantic import BaseModel, ValidationError

from statesman.utils.config_utils import hash_config_section
from statesman.utils.file_utils import get_file_mtime

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

    def __init__(self, config_path: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)  # Set global logging to INFO for verbosity
        self.config_path = Path(config_path).resolve()
        self.logger.info(f"Initializing Statesman with config: {self.config_path}")
        self.config = self.load_config()
        workdir_str = self.config.get('workdir', '.')
        self.workdir = (self.config_path.parent / Path(workdir_str)).resolve()
        if not self.workdir.exists():
            self.logger.info(f"Workdir {self.workdir} does not exist. Creating it.")
            self.workdir.mkdir(parents=True, exist_ok=True)
        else:
            self.logger.info(f"Workdir {self.workdir} already exists.")
        self.state_file = self.workdir / ".statesman_state.yaml"
        self.previous_states = self.load_previous_states()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        self.logger.info(f"Loading config from {self.config_path}")
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def load_previous_states(self) -> Dict[str, str]:
        """Load previous state hashes from file."""
        if self.state_file.exists():
            self.logger.info(f"Loading previous states from {self.state_file}")
            with open(self.state_file) as f:
                return yaml.safe_load(f) or {}
        self.logger.info("No previous states found.")
        return {}

    def save_state(self, section: str, hash_value: str):
        """Save state hash for a section."""
        self.logger.info(f"Saving state for section '{section}' with hash {hash_value}")
        self.previous_states[section] = hash_value
        with open(self.state_file, "w") as f:
            yaml.safe_dump(self.previous_states, f)

    def has_section_changed(self, section: str) -> bool:
        """Check if a config section has changed."""
        current_hash = hash_config_section(self.config.get(section, {}))
        previous_hash = self.previous_states.get(section)
        changed = current_hash != previous_hash
        self.logger.info(f"Section '{section}' changed: {changed} (current: {current_hash}, previous: {previous_hash})")
        return changed

    def needs_run(self) -> bool:
        """Determine if the step needs to be run based on inputs, outputs, and sections."""
        self.logger.info("Checking if step needs to run.")
        # Check inputs
        for mf in self.input_files:
            path = self.workdir / mf.name
            newer_than = self.config_path if mf.newer_than == 'config' else mf.newer_than
            try:
                state = FileState(path=path, non_empty=mf.non_empty, newer_than=newer_than)
                self.logger.info(f"Input file '{path}' is valid.")
            except ValidationError as e:
                self.logger.warning(f"Input file '{path}' invalid: {e}. Needs run.")
                return True

        # Check if any output is missing
        for out_name in self.output_files:
            out_path = self.workdir / out_name
            if not out_path.exists() or out_path.stat().st_size == 0:
                self.logger.warning(f"Output file '{out_path}' is missing or empty. Needs run.")
                return True
            self.logger.info(f"Output file '{out_path}' exists and is non-empty.")

        # Check if any input is newer than any output
        for out_name in self.output_files:
            out_path = self.workdir / out_name
            out_mtime = get_file_mtime(out_path)
            for mf in self.input_files:
                in_path = self.workdir / mf.name
                in_mtime = get_file_mtime(in_path)
                if in_mtime > out_mtime:
                    self.logger.warning(f"Input '{in_path}' is newer than output '{out_path}'. Needs run.")
                    return True

        # Check if any dependent section changed
        for section in self.dependent_sections:
            if self.has_section_changed(section):
                self.logger.warning(f"Dependent section '{section}' has changed. Needs run.")
                return True

        self.logger.info("No changes detected. Step does not need to run.")
        return False

    def run(self):
        """Run the step if necessary and update states."""
        self.logger.info("Starting run check.")
        if self.needs_run():
            self.logger.info("Step needs to run. Executing...")
            self._execute()
            self.logger.info("Execution completed.")
            # Update states for dependent sections
            for section in self.dependent_sections:
                current_hash = hash_config_section(self.config.get(section, {}))
                self.save_state(section, current_hash)
            # Validate outputs after execution
            for out_name in self.output_files:
                out_path = self.workdir / out_name
                if not out_path.exists() or out_path.stat().st_size == 0:
                    error_msg = f"Output file '{out_path}' was not created properly."
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)
                self.logger.info(f"Output file '{out_path}' validated successfully.")
        else:
            self.logger.info("Step does not need to run.")

    def _execute(self):
        """User-defined execution logic. Subclasses should override this."""
        raise NotImplementedError("Subclasses must implement _execute method.")
