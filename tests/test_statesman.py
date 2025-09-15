"""Tests for statesman."""

import time
import pytest
from pathlib import Path
from statesman.core.base import Statesman, ManagedFile
from statesman.models.state import FileState
from statesman.utils.config_utils import hash_config_section
from statesman.utils.file_utils import get_file_mtime, is_file_non_empty


@pytest.fixture
def temp_dir(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("workdir: work_dir\ntest: value")
    return tmp_path, config


def test_file_state_validation(temp_dir):
    tmp_path, config = temp_dir
    time.sleep(0.01)  # Ensure file is created after config for mtime difference
    file = tmp_path / "test.txt"
    file.write_text("data")
    state = FileState(path=file, newer_than=config)
    assert state.path == file


def test_file_state_validation_errors(tmp_path):
    non_existent = tmp_path / "missing.txt"
    with pytest.raises(ValueError, match="File does not exist"):
        FileState(path=non_existent)

    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    with pytest.raises(ValueError, match="File is empty"):
        FileState(path=empty_file, non_empty=True)

    old_file = tmp_path / "old.txt"
    old_file.write_text("data")
    time.sleep(1)
    new_file = tmp_path / "new.txt"
    new_file.write_text("data")
    with pytest.raises(ValueError, match="File .* is not newer than"):
        FileState(path=old_file, newer_than=new_file)


def test_statesman_init(temp_dir):
    tmp_path, config = temp_dir
    sm = Statesman(str(config))
    assert sm.config == {"workdir": "work_dir", "test": "value"}
    assert sm.workdir == tmp_path / "work_dir"


def test_workdir_creation(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: new_work_dir")
    sm = Statesman(str(config_path))
    assert sm.workdir.exists()
    assert sm.workdir.is_dir()


def test_hash_config_section():
    section = {"key": "value"}
    hash1 = hash_config_section(section)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hex
    hash2 = hash_config_section(section)
    assert hash1 == hash2
    different = {"key": "different"}
    assert hash_config_section(different) != hash1
    # Test with nested dict
    nested = {"a": {"b": 1, "c": 2}}
    hash_nested = hash_config_section(nested)
    # Same nested but different order
    nested_reordered = {"a": {"c": 2, "b": 1}}
    assert hash_config_section(nested_reordered) == hash_nested
    # Test with float keys
    section_float = {1.0: "value", 2.0: "other"}
    hash_float = hash_config_section(section_float)
    assert isinstance(hash_float, str)
    # Same float keys different order
    section_float_reordered = {2.0: "other", 1.0: "value"}
    assert hash_config_section(section_float_reordered) == hash_float
    # Test float precision
    section_float_prec = {1.0000000001: "value"}
    assert hash_config_section(section_float_prec) == hash_config_section({1.0: "value"})


def test_file_utils(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.touch()
    assert not is_file_non_empty(empty)

    non_empty = tmp_path / "non_empty.txt"
    non_empty.write_text("data")
    assert is_file_non_empty(non_empty)

    missing = tmp_path / "missing.txt"
    assert get_file_mtime(missing) == 0.0

    assert get_file_mtime(non_empty) > 0


class TestStep(Statesman):
    __test__ = False
    dependent_sections = ["test"]
    output_files = ["output.txt"]
    input_files = [ManagedFile(name="input.txt", non_empty=True, newer_than="config")]

    def _execute(self):
        (self.workdir / "output.txt").write_text("executed")


def test_has_section_changed(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: initial")
    sm = TestStep(str(config_path))
    assert sm.has_section_changed("test")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.has_section_changed("test")
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: changed")
    sm.config = sm.load_config()  # Reload config
    assert sm.has_section_changed("test")


def test_has_section_changed_with_nested_dict(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    a: 1\n    b: 2")
    sm = TestStep(str(config_path))
    assert sm.has_section_changed("test")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.has_section_changed("test")
    # Change order of nested keys
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    b: 2\n    a: 1")
    sm.config = sm.load_config()  # Reload config
    assert not sm.has_section_changed("test")  # Should not detect change due to key order
    # Change a value
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    a: 1\n    b: 3")
    sm.config = sm.load_config()
    assert sm.has_section_changed("test")


def test_needs_run_scenarios(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir")
    sm = TestStep(str(config_path))
    time.sleep(1)  # Ensure subsequent file operations have later timestamps

    # Missing input
    assert sm.needs_run()  # Input missing

    # Create input
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")
    time.sleep(1)  # Ensure input mtime > config mtime

    # Missing output
    assert sm.needs_run()

    # Create output
    output_path = sm.workdir / "output.txt"
    output_path.write_text("data")
    time.sleep(1)  # Ensure output mtime > input mtime

    # Changed section (initially no state)
    assert sm.needs_run()

    # Save state
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.needs_run()

    # Change section
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: changed")
    time.sleep(1)  # Ensure config mtime is distinct
    sm.config = sm.load_config()
    assert sm.needs_run()

    # Simulate updating input after config change to make it newer than config
    time.sleep(1)
    input_path.touch()

    # Run the step to reset state and update outputs
    sm.run()
    assert not sm.needs_run()

    # Test input newer than output
    time.sleep(1)
    input_path.touch()
    assert sm.needs_run()


def test_run_executes(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: value")
    sm = TestStep(str(config_path))

    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")

    sm.run()
    output_path = sm.workdir / "output.txt"
    assert output_path.exists()
    assert output_path.read_text() == "executed"
    assert not sm.needs_run()  # After run, shouldn't need to run again

    # Test if it doesn't run again
    output_path.write_text("unchanged")
    sm.run()
    assert output_path.read_text() == "unchanged"  # Not overwritten


def test_run_output_validation_failure(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir")
    class FailingStep(Statesman):
        output_files = ["output.txt"]
        def _execute(self):
            pass  # Doesn't create output

    sm = FailingStep(str(config_path))
    with pytest.raises(RuntimeError, match=r"Output file '.*/output\.txt' was not created properly\."):
        sm.run()
