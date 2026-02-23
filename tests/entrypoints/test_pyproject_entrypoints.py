"""Tests for PyprojectTomlEntrypointPatcher."""

import tomllib
from pathlib import Path

import pytest

from invenio_integration_tests.entrypoints import (
    EntryPoint,
    PyprojectTomlEntrypointPatcher,
)


@pytest.fixture
def basic_pyproject_toml(tmp_path: Path) -> Path:
    """Create a basic pyproject.toml file with entrypoints in dict format."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test-package"
version = "1.0.0"

[project.entry-points.pytest11]
my_plugin = "my_package:main"
other_plugin = "my_package:other"

[project.entry-points."invenio_base.apps"]
test_app = "my_package.app:TestApp"
"""
    )
    return pyproject


@pytest.fixture
def list_format_pyproject_toml(tmp_path: Path) -> Path:
    """Create a pyproject.toml file with entrypoints in list format."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test-package"
version = "1.0.0"

[project.entry-points]
pytest11 = [
    "my_plugin=my_package:main",
    "other_plugin=my_package:other",
]
"invenio_base.apps" = [
    "test_app=my_package.app:TestApp",
]
"""
    )
    return pyproject


@pytest.fixture
def empty_pyproject_toml(tmp_path: Path) -> Path:
    """Create an empty pyproject.toml file without entrypoints."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test-package"
version = "1.0.0"
"""
    )
    return pyproject


def test_load_parses_dict_format_entrypoints(basic_pyproject_toml: Path):
    """Test that load() correctly parses dict-format entrypoints from pyproject.toml."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    assert "pytest11" in patcher.entrypoints
    assert "invenio_base.apps" in patcher.entrypoints
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"
    assert patcher.entrypoints["pytest11"]["other_plugin"] == "my_package:other"
    assert (
        patcher.entrypoints["invenio_base.apps"]["test_app"] == "my_package.app:TestApp"
    )


def test_load_parses_list_format_entrypoints(list_format_pyproject_toml: Path):
    """Test that load() correctly parses list-format entrypoints from pyproject.toml."""
    patcher = PyprojectTomlEntrypointPatcher(list_format_pyproject_toml)

    assert "pytest11" in patcher.entrypoints
    assert "invenio_base.apps" in patcher.entrypoints
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"
    assert patcher.entrypoints["pytest11"]["other_plugin"] == "my_package:other"
    assert (
        patcher.entrypoints["invenio_base.apps"]["test_app"] == "my_package.app:TestApp"
    )


def test_load_handles_empty_file(empty_pyproject_toml: Path):
    """Test that load() handles files without entrypoints section."""
    patcher = PyprojectTomlEntrypointPatcher(empty_pyproject_toml)

    assert patcher.entrypoints == {}


def test_add_entrypoint_to_existing_group(basic_pyproject_toml: Path):
    """Test adding an entrypoint to an existing group."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.add_entrypoint(EntryPoint("pytest11", "new_plugin", "my_package:new"))

    assert patcher.entrypoints["pytest11"]["new_plugin"] == "my_package:new"
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"


def test_add_entrypoint_to_new_group(basic_pyproject_toml: Path):
    """Test adding an entrypoint to a new group."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.add_entrypoint(EntryPoint("flask.commands", "my_command", "my_package.cli"))

    assert "flask.commands" in patcher.entrypoints
    assert patcher.entrypoints["flask.commands"]["my_command"] == "my_package.cli"


def test_add_entrypoint_replaces_existing(basic_pyproject_toml: Path):
    """Test that adding an entrypoint replaces existing one with same name."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    original_value = patcher.entrypoints["pytest11"]["my_plugin"]
    patcher.add_entrypoint(EntryPoint("pytest11", "my_plugin", "new_package:new_main"))

    assert patcher.entrypoints["pytest11"]["my_plugin"] == "new_package:new_main"
    assert original_value != patcher.entrypoints["pytest11"]["my_plugin"]


def test_add_entrypoint_raises_on_none_value(basic_pyproject_toml: Path):
    """Test that adding an entrypoint with None value raises ValueError."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    with pytest.raises(ValueError, match="Cannot add entrypoint.*with None value"):
        patcher.add_entrypoint(EntryPoint("pytest11", "test", None))


def test_remove_entrypoint(basic_pyproject_toml: Path):
    """Test removing a specific entrypoint."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.remove_entrypoint(EntryPoint("pytest11", "my_plugin", None), set())

    assert "my_plugin" not in patcher.entrypoints["pytest11"]
    assert "other_plugin" in patcher.entrypoints["pytest11"]


def test_remove_entrypoint_removes_empty_group(basic_pyproject_toml: Path):
    """Test that removing last entrypoint in a group removes the group."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.remove_entrypoint(EntryPoint("invenio_base.apps", "test_app", None), set())

    assert "invenio_base.apps" not in patcher.entrypoints


def test_remove_entrypoint_respects_kept_entrypoints(basic_pyproject_toml: Path):
    """Test that remove_entrypoint doesn't remove kept entrypoints."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    kept = {EntryPoint("pytest11", "my_plugin", None)}
    patcher.remove_entrypoint(EntryPoint("pytest11", "my_plugin", None), kept)

    assert "my_plugin" in patcher.entrypoints["pytest11"]


def test_remove_all_entrypoints(basic_pyproject_toml: Path):
    """Test removing all entrypoints."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.remove_all_entrypoints(set())

    assert patcher.entrypoints == {}


def test_remove_all_entrypoints_keeps_specified(basic_pyproject_toml: Path):
    """Test that remove_all_entrypoints keeps specified entrypoints."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    kept = {
        EntryPoint("pytest11", "my_plugin", None),
        EntryPoint("invenio_base.apps", "test_app", None),
    }
    patcher.remove_all_entrypoints(kept)

    assert "pytest11" in patcher.entrypoints
    assert "invenio_base.apps" in patcher.entrypoints
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"
    assert "other_plugin" not in patcher.entrypoints["pytest11"]
    assert (
        patcher.entrypoints["invenio_base.apps"]["test_app"] == "my_package.app:TestApp"
    )


def test_save_writes_to_file(basic_pyproject_toml: Path):
    """Test that save() writes entrypoints back to the file."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.add_entrypoint(EntryPoint("pytest11", "new_plugin", "my_package:new"))
    patcher.save()

    # Reload and verify
    patcher2 = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)
    assert patcher2.entrypoints["pytest11"]["new_plugin"] == "my_package:new"


def test_save_creates_section_if_missing(empty_pyproject_toml: Path):
    """Test that save() creates the entry-points section if it doesn't exist."""
    patcher = PyprojectTomlEntrypointPatcher(empty_pyproject_toml)

    patcher.add_entrypoint(EntryPoint("pytest11", "my_plugin", "my_package:main"))
    patcher.save()

    # Reload and verify
    patcher2 = PyprojectTomlEntrypointPatcher(empty_pyproject_toml)
    assert patcher2.entrypoints["pytest11"]["my_plugin"] == "my_package:main"


def test_save_uses_dict_format(basic_pyproject_toml: Path):
    """Test that save() uses dict format for entrypoints."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.add_entrypoint(EntryPoint("pytest11", "test", "value"))
    patcher.save()

    # Check that the file contains dict-formatted entrypoints
    with basic_pyproject_toml.open("rb") as f:
        data = tomllib.load(f)

    assert isinstance(data["project"]["entry-points"]["pytest11"], dict)
    assert data["project"]["entry-points"]["pytest11"]["test"] == "value"


def test_save_removes_empty_entrypoints_section(basic_pyproject_toml: Path):
    """Test that save() removes the entry-points section if all entrypoints are removed."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    patcher.remove_all_entrypoints(set())
    patcher.save()

    # Check that entry-points section is gone
    with basic_pyproject_toml.open("rb") as f:
        data = tomllib.load(f)

    assert "entry-points" not in data["project"]


def test_load_handles_various_whitespace_in_list_format(tmp_path: Path):
    """Test that load() handles various whitespace formats in list-format entrypoints."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test"

[project.entry-points]
pytest11 = [
    "plugin1=package:main",
    "plugin2 = package:main2",
    "plugin3  =  package:main3",
]
"""
    )

    patcher = PyprojectTomlEntrypointPatcher(pyproject)

    assert patcher.entrypoints["pytest11"]["plugin1"] == "package:main"
    assert patcher.entrypoints["pytest11"]["plugin2"] == "package:main2"
    assert patcher.entrypoints["pytest11"]["plugin3"] == "package:main3"


def test_parse_entrypoint_value_raises_on_invalid_format(tmp_path: Path):
    """Test that _parse_entrypoint_value raises on invalid format."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test"

[project.entry-points]
pytest11 = ["invalid_format_no_equals"]
"""
    )

    with pytest.raises(ValueError, match="Invalid entrypoint format"):
        PyprojectTomlEntrypointPatcher(pyproject)


def test_apply_patches_complex_scenario(basic_pyproject_toml: Path):
    """Test a complex scenario with multiple operations."""
    patcher = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    # Remove one entrypoint, add two new ones
    patcher.remove_entrypoint(EntryPoint("pytest11", "other_plugin", None), set())
    patcher.add_entrypoint(EntryPoint("pytest11", "new1", "pkg:func1"))
    patcher.add_entrypoint(
        EntryPoint("flask.commands", "plugin", "pkg.commands:Plugin")
    )

    assert "other_plugin" not in patcher.entrypoints["pytest11"]
    assert patcher.entrypoints["pytest11"]["new1"] == "pkg:func1"
    assert patcher.entrypoints["flask.commands"]["plugin"] == "pkg.commands:Plugin"
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"


def test_roundtrip_preserves_data(basic_pyproject_toml: Path):
    """Test that loading and saving preserves entrypoint data."""
    # Load original
    patcher1 = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)
    original_entrypoints = dict(patcher1.entrypoints)

    # Save without modifications
    patcher1.save()

    # Reload and compare
    patcher2 = PyprojectTomlEntrypointPatcher(basic_pyproject_toml)

    assert patcher2.entrypoints == original_entrypoints


def test_list_format_roundtrip(list_format_pyproject_toml: Path):
    """Test that list format is converted to dict format on save."""
    patcher = PyprojectTomlEntrypointPatcher(list_format_pyproject_toml)

    # Make a change and save
    patcher.add_entrypoint(EntryPoint("pytest11", "new_plugin", "pkg:new"))
    patcher.save()

    # Reload and check format
    with list_format_pyproject_toml.open("rb") as f:
        data = tomllib.load(f)

    # After save, it should be dict format
    assert isinstance(data["project"]["entry-points"]["pytest11"], dict)
    assert data["project"]["entry-points"]["pytest11"]["new_plugin"] == "pkg:new"


def test_handles_missing_project_section(tmp_path: Path):
    """Test that save() creates project section if it doesn't exist."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[build-system]
requires = ["setuptools"]
"""
    )

    patcher = PyprojectTomlEntrypointPatcher(pyproject)
    patcher.add_entrypoint(EntryPoint("pytest11", "plugin", "pkg:main"))
    patcher.save()

    # Reload and verify
    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    assert "project" in data
    assert "entry-points" in data["project"]
    assert data["project"]["entry-points"]["pytest11"]["plugin"] == "pkg:main"
