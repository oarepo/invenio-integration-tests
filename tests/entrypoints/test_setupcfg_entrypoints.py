"""Tests for SetupCfgEntrypointPatcher."""

from pathlib import Path

import pytest

from invenio_integration_tests.entrypoints import (
    EntryPoint,
    SetupCfgEntrypointPatcher,
)


@pytest.fixture
def basic_setup_cfg(tmp_path: Path) -> Path:
    """Create a basic setup.cfg file with entrypoints."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text(
        """[metadata]
name = test-package
version = 1.0.0

[options.entry_points]
pytest11 =
    my_plugin = my_package:main
    other_plugin = my_package:other
invenio_base.apps =
    test_app = my_package.app:TestApp
"""
    )
    return setup_cfg


@pytest.fixture
def empty_setup_cfg(tmp_path: Path) -> Path:
    """Create an empty setup.cfg file without entrypoints."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text(
        """[metadata]
name = test-package
version = 1.0.0
"""
    )
    return setup_cfg


def test_load_parses_entrypoints(basic_setup_cfg: Path):
    """Test that load() correctly parses entrypoints from setup.cfg."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    assert "pytest11" in patcher.entrypoints
    assert "invenio_base.apps" in patcher.entrypoints
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"
    assert patcher.entrypoints["pytest11"]["other_plugin"] == "my_package:other"
    assert (
        patcher.entrypoints["invenio_base.apps"]["test_app"] == "my_package.app:TestApp"
    )


def test_load_handles_empty_file(empty_setup_cfg: Path):
    """Test that load() handles files without entrypoints section."""
    patcher = SetupCfgEntrypointPatcher(empty_setup_cfg)

    assert patcher.entrypoints == {}


def test_add_entrypoint_to_existing_group(basic_setup_cfg: Path):
    """Test adding an entrypoint to an existing group."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.add_entrypoint(EntryPoint("pytest11", "new_plugin", "my_package:new"))

    assert patcher.entrypoints["pytest11"]["new_plugin"] == "my_package:new"
    assert patcher.entrypoints["pytest11"]["my_plugin"] == "my_package:main"


def test_add_entrypoint_to_new_group(basic_setup_cfg: Path):
    """Test adding an entrypoint to a new group."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.add_entrypoint(EntryPoint("flask.commands", "my_command", "my_package.cli"))

    assert "flask.commands" in patcher.entrypoints
    assert patcher.entrypoints["flask.commands"]["my_command"] == "my_package.cli"


def test_add_entrypoint_replaces_existing(basic_setup_cfg: Path):
    """Test that adding an entrypoint replaces existing one with same name."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    original_value = patcher.entrypoints["pytest11"]["my_plugin"]
    patcher.add_entrypoint(EntryPoint("pytest11", "my_plugin", "new_package:new_main"))

    assert patcher.entrypoints["pytest11"]["my_plugin"] == "new_package:new_main"
    assert original_value != patcher.entrypoints["pytest11"]["my_plugin"]


def test_add_entrypoint_raises_on_none_value(basic_setup_cfg: Path):
    """Test that adding an entrypoint with None value raises ValueError."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    with pytest.raises(ValueError, match="Cannot add entrypoint.*with None value"):
        patcher.add_entrypoint(EntryPoint("pytest11", "test", None))


def test_remove_entrypoint(basic_setup_cfg: Path):
    """Test removing a specific entrypoint."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.remove_entrypoint(EntryPoint("pytest11", "my_plugin", None), set())

    assert "my_plugin" not in patcher.entrypoints["pytest11"]
    assert "other_plugin" in patcher.entrypoints["pytest11"]


def test_remove_entrypoint_removes_empty_group(basic_setup_cfg: Path):
    """Test that removing last entrypoint in a group removes the group."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.remove_entrypoint(EntryPoint("invenio_base.apps", "test_app", None), set())

    assert "invenio_base.apps" not in patcher.entrypoints


def test_remove_entrypoint_respects_kept_entrypoints(basic_setup_cfg: Path):
    """Test that remove_entrypoint doesn't remove kept entrypoints."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    kept = {EntryPoint("pytest11", "my_plugin", None)}
    patcher.remove_entrypoint(EntryPoint("pytest11", "my_plugin", None), kept)

    assert "my_plugin" in patcher.entrypoints["pytest11"]


def test_remove_all_entrypoints(basic_setup_cfg: Path):
    """Test removing all entrypoints."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.remove_all_entrypoints(set())

    assert patcher.entrypoints == {}


def test_remove_all_entrypoints_keeps_specified(basic_setup_cfg: Path):
    """Test that remove_all_entrypoints keeps specified entrypoints."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

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


def test_save_writes_to_file(basic_setup_cfg: Path):
    """Test that save() writes entrypoints back to the file."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.add_entrypoint(EntryPoint("pytest11", "new_plugin", "my_package:new"))
    patcher.save()

    # Reload and verify
    patcher2 = SetupCfgEntrypointPatcher(basic_setup_cfg)
    assert patcher2.entrypoints["pytest11"]["new_plugin"] == "my_package:new"


def test_save_creates_section_if_missing(empty_setup_cfg: Path):
    """Test that save() creates the entry_points section if it doesn't exist."""
    patcher = SetupCfgEntrypointPatcher(empty_setup_cfg)

    patcher.add_entrypoint(EntryPoint("pytest11", "my_plugin", "my_package:main"))
    patcher.save()

    # Reload and verify
    patcher2 = SetupCfgEntrypointPatcher(empty_setup_cfg)
    assert patcher2.entrypoints["pytest11"]["my_plugin"] == "my_package:main"


def test_save_preserves_formatting(basic_setup_cfg: Path):
    """Test that save() formats entrypoints with spaces around equals sign."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

    patcher.add_entrypoint(EntryPoint("pytest11", "test", "value"))
    patcher.save()

    # Check that the file contains properly formatted entrypoints
    content = basic_setup_cfg.read_text()
    assert "test = value" in content


def test_load_handles_various_whitespace(tmp_path: Path):
    """Test that load() handles various whitespace formats in entrypoints."""
    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.write_text(
        """[options.entry_points]
pytest11 =
    plugin1=package:main
    plugin2 = package:main2
    plugin3  =  package:main3
"""
    )

    patcher = SetupCfgEntrypointPatcher(setup_cfg)

    assert patcher.entrypoints["pytest11"]["plugin1"] == "package:main"
    assert patcher.entrypoints["pytest11"]["plugin2"] == "package:main2"
    assert patcher.entrypoints["pytest11"]["plugin3"] == "package:main3"


def test_apply_patches_complex_scenario(basic_setup_cfg: Path):
    """Test a complex scenario with multiple operations."""
    patcher = SetupCfgEntrypointPatcher(basic_setup_cfg)

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
