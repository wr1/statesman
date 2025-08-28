"""Tests for statesman."""

import pytest
from statesman.core.base import Statesman
from statesman.models.state import FileState


@pytest.fixture
def temp_dir(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("test: value")
    return tmp_path, config


def test_file_state_validation(temp_dir):
    tmp_path, config = temp_dir
    file = tmp_path / "test.txt"
    file.write_text("data")
    state = FileState(path=file, newer_than=config)
    assert state.path == file


def test_statesman_init(temp_dir):
    tmp_path, config = temp_dir
    sm = Statesman(str(tmp_path), str(config))
    assert sm.config == {"test": "value"}
