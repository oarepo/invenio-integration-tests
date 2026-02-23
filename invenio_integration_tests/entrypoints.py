"""
Entrypoint patching utilities for both setup.cfg and pyproject.toml files.

This module provides a clean, object-oriented interface for modifying entrypoints
in Python packages, supporting both legacy setup.cfg and modern pyproject.toml formats.
"""

import re
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import NamedTuple

import tomli_w
from configupdater import ConfigUpdater, Option


class EntryPoint(NamedTuple):
    """Represents a single entry point."""

    group: str
    name: str
    value: str | None


class EntrypointPatcher(ABC):
    """
    Abstract base class for patching entrypoints in Python package configuration files.

    Subclasses must implement methods for reading, writing, and parsing entrypoints
    in their respective file formats (setup.cfg or pyproject.toml).

    The patching logic is implemented in the base class, while file-format-specific
    operations are delegated to concrete subclasses.
    """

    entrypoints: dict[str, dict[str, str]]  # group -> name -> value mapping

    def __init__(self, file_path: Path):
        """
        Initialize the patcher with a configuration file path.

        Args:
            file_path: Path to the configuration file (setup.cfg or pyproject.toml)
        """
        self.file_path = file_path
        self.load()

    @abstractmethod
    def load(self) -> None:
        """
        Load the config file and parse the entrypoints.
        Set up the self.entrypoints attribute with a standard dictionary format.

        Returns:
            A dictionary mapping group names to dictionaries of entrypoint names and values.
            Format: {"group_name": {"entrypoint_name": "entrypoint_value", ...}, ...}
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """
        Write entrypoints from the standard format to the internal representation.

        Args:
            entrypoints: Dictionary mapping group names to entrypoint name-value pairs.
                        Format: {"group_name": {"entrypoint_name": "entrypoint_value", ...}, ...}
        """
        pass

    def remove_all_entrypoints(self, kept_entrypoints: set[EntryPoint]) -> None:
        """
        Remove all entrypoints except those in the kept set.

        Args:
            kept_entrypoints: Set of entrypoints to preserve
        """
        # Build new entrypoints with only kept entries
        new_entrypoints: dict[str, dict[str, str]] = {}
        for group, entries in self.entrypoints.items():
            kept_in_group = {ep.name for ep in kept_entrypoints if ep.group == group}
            if kept_in_group:
                new_entrypoints[group] = {
                    name: value
                    for name, value in entries.items()
                    if name in kept_in_group
                }

        self.entrypoints = new_entrypoints

    def remove_entrypoint(
        self, entry: EntryPoint, kept_entrypoints: set[EntryPoint]
    ) -> None:
        """
        Remove a specific entrypoint unless it's in the kept set.

        Args:
            entry: The entrypoint to remove
            kept_entrypoints: Set of entrypoints to preserve
        """
        if entry in kept_entrypoints:
            return

        if (
            entry.group in self.entrypoints
            and entry.name in self.entrypoints[entry.group]
        ):
            del self.entrypoints[entry.group][entry.name]
            # Remove empty groups
            if not self.entrypoints[entry.group]:
                del self.entrypoints[entry.group]

    def add_entrypoint(self, entry: EntryPoint) -> None:
        """
        Add a new entrypoint, replacing any existing one with the same group and name.

        Args:
            entry: The entrypoint to add

        Raises:
            ValueError: If entry.value is None
        """
        if entry.value is None:
            raise ValueError(
                f"Cannot add entrypoint {entry.group}:{entry.name} with None value"
            )

        # Ensure the group exists
        if entry.group not in self.entrypoints:
            self.entrypoints[entry.group] = {}

        # Add or replace the entrypoint
        self.entrypoints[entry.group][entry.name] = entry.value

    def apply_patches(
        self, remove: list[dict], keep: list[dict], add: list[dict]
    ) -> None:
        """
        Apply a series of entrypoint patches.

        Args:
            remove: List of entrypoints to remove (or ["*"] to remove all)
            keep: List of entrypoints to keep when removing all
            add: List of entrypoints to add
        """
        # Build the set of entrypoints to keep
        kept_entrypoints: set[EntryPoint] = set()
        for ep in keep:
            kept_entrypoints.add(EntryPoint(ep["group"], ep["name"], None))

        # Process removals
        for ep in remove:
            if ep == "*":
                self.remove_all_entrypoints(kept_entrypoints)
            else:
                self.remove_entrypoint(
                    EntryPoint(ep["group"], ep["name"], None), kept_entrypoints
                )

        # Process additions
        for ep in add:
            self.add_entrypoint(EntryPoint(ep["group"], ep["name"], ep["value"]))


class SetupCfgEntrypointPatcher(EntrypointPatcher):
    """Entrypoint patcher for setup.cfg files using ConfigUpdater."""

    def load(self) -> None:
        """Load and parse the setup.cfg file."""
        self.cfg = ConfigUpdater()
        self.cfg.read_string(self.file_path.read_text())

        self.entrypoints = {}

        if "options.entry_points" not in self.cfg:
            return

        eps = self.cfg["options.entry_points"]
        for group, values in eps.items():
            values_list = self._load_values(values)
            self.entrypoints[group] = {}

            for val in values_list:
                # Parse "name=value" format
                if "=" in val:
                    name, value = val.split("=", 1)
                    self.entrypoints[group][name.strip()] = value.strip()

    def save(self) -> None:
        """Write the modified configuration back to setup.cfg."""
        if "options.entry_points" not in self.cfg:
            self.cfg.add_section("options.entry_points")

        eps = self.cfg["options.entry_points"]

        # Remove all existing groups
        for group in list(eps.keys()):
            del eps[group]

        # Add new groups and entrypoints
        for group, entries in self.entrypoints.items():
            if entries:  # Only add non-empty groups
                eps[group] = ""
                values = [f"{name}={value}" for name, value in entries.items()]
                self._write_values(eps[group], values)

        with self.file_path.open("w") as f:
            self.cfg.write(f)

    def _load_values(self, option: Option) -> list[str]:
        """
        Load and normalize entrypoint values from a ConfigUpdater option.

        Args:
            option: The ConfigUpdater option to load values from

        Returns:
            List of normalized entrypoint strings (whitespace removed)
        """
        return [x.strip().replace(" ", "") for x in option.as_list() if x.strip()]

    def _write_values(self, option: Option, values: list[str]) -> None:
        """
        Write entrypoint values to a ConfigUpdater option with proper formatting.

        Args:
            option: The ConfigUpdater option to write to
            values: List of entrypoint strings to write
        """
        # Format with spaces around '=' for readability
        formatted_values = [val.replace("=", " = ") for val in values]
        option.set_values(formatted_values)


class PyprojectTomlEntrypointPatcher(EntrypointPatcher):
    """Entrypoint patcher for pyproject.toml files."""

    def load(self) -> None:
        """Load and parse the pyproject.toml file."""
        with self.file_path.open("rb") as f:
            self.data = tomllib.load(f)

        self.entrypoints: dict[str, dict[str, str]] = {}

        if "project" not in self.data or "entry-points" not in self.data["project"]:
            return

        eps = self.data["project"]["entry-points"]

        for group, values in eps.items():
            self.entrypoints[group] = {}

            if isinstance(values, dict):
                # Format: [project.entry-points.group]
                #         name = "value"
                self.entrypoints[group] = dict(values)
            elif isinstance(values, list):
                # Format: [project.entry-points.group]
                #         ["name=value", ...]
                for val in values:
                    name, value = self._parse_entrypoint_value(val)
                    self.entrypoints[group][name] = value

    def save(self) -> None:
        """Write the modified configuration back to pyproject.toml."""
        if "project" not in self.data:
            self.data["project"] = {}

        # Replace the entire entry-points section
        if self.entrypoints:
            self.data["project"]["entry-points"] = self.entrypoints
        else:
            # Remove entry-points section if empty
            if "entry-points" in self.data["project"]:
                del self.data["project"]["entry-points"]

        with self.file_path.open("wb") as f:
            tomli_w.dump(self.data, f)

    def _parse_entrypoint_value(self, value: str) -> tuple[str, str]:
        """
        Parse an entrypoint value string into name and value.

        Args:
            value: String in format "name=value" or "name = value"

        Returns:
            Tuple of (name, value)
        """
        # Handle both "name=value" and "name = value" formats
        match = re.match(r"(.*?)\s*=\s*(.*)", value)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        raise ValueError(f"Invalid entrypoint format: {value}")


def apply_entrypoint_patches(
    pkg_path: Path,
    remove: list[dict] | list[str] | None = None,
    keep: list[dict] | None = None,
    add: list[dict] | None = None,
) -> None:
    """
    Apply entry point patches to the package at the given path.

    This function automatically detects whether the package uses setup.cfg or
    pyproject.toml and applies the appropriate patches.

    Args:
        pkg_path: Path to the package directory
        remove: List of entrypoints to remove. Can be:
                - A list of dicts: [{"group": "...", "name": "..."}]
                - ["*"] to remove all entrypoints
                - None for no removals
        keep: List of entrypoints to keep when removing all:
              [{"group": "...", "name": "..."}]
        add: List of entrypoints to add:
             [{"group": "...", "name": "...", "value": "..."}]

    Examples:
        # Remove all entrypoints except one, and add a new one
        apply_entrypoint_patches(
            Path("/path/to/package"),
            remove=["*"],
            keep=[{"group": "console_scripts", "name": "my_script"}],
            add=[{
                "group": "invenio_base.apps",
                "name": "my_app",
                "value": "my_package.app:MyApp"
            }]
        )

        # Just add an entrypoint
        apply_entrypoint_patches(
            Path("/path/to/package"),
            add=[{
                "group": "console_scripts",
                "name": "my_command",
                "value": "my_package.cli:main"
            }]
        )

    Raises:
        FileNotFoundError: If neither setup.cfg nor pyproject.toml is found
    """
    # Try to find the configuration file
    setup_cfg = pkg_path / "setup.cfg"
    pyproject_toml = pkg_path / "pyproject.toml"

    # Create the appropriate patcher based on file type
    patcher: EntrypointPatcher
    if setup_cfg.exists():
        patcher = SetupCfgEntrypointPatcher(setup_cfg)
    elif pyproject_toml.exists():
        patcher = PyprojectTomlEntrypointPatcher(pyproject_toml)
    else:
        raise FileNotFoundError(f"No setup.cfg or pyproject.toml found in {pkg_path}")

    # Normalize remove parameter - handle ["*"] special case
    remove_list: list[dict] = []
    if remove:
        if remove == ["*"] or (len(remove) == 1 and remove[0] == "*"):
            remove_list = ["*"]  # type: ignore
        else:
            remove_list = remove  # type: ignore

    # Apply changes and save
    patcher.apply_patches(remove=remove_list, keep=keep or [], add=add or [])
    patcher.save()
