"""Version propagation logic for oarepo releases."""

import re
from copy import replace
from typing import cast

from packaging.version import Version


def parse_local_rdm_version(local: str) -> tuple[int, Version] | None:
    """
    Parse local version in format '<ordinal>.rdm.<version>'.

    Returns:
        Tuple of (ordinal, rdm_version) or None if format doesn't match
    """
    if not local:
        return None

    # Match pattern: <ordinal>.rdm.<version>
    match = re.match(r"^(\d+)\.rdm\.(.+)$", local)
    if not match:
        return None

    ordinal = int(match.group(1))
    rdm_version_str = match.group(2)

    try:
        rdm_version = Version(rdm_version_str)
        return (ordinal, rdm_version)
    except Exception:
        return None


def propagate_version(oarepo_version: Version, app_rdm_version: Version) -> Version:
    """
    Propagate version from app-rdm to oarepo.

    The oarepo version may contain a local version in format '+<ordinal>.rdm.<previous_rdm_version>'.

    Rules:
    - If local version exists with rdm tracking:
      1. Extract the previous rdm version
      2. Compare fields (minor, micro, a, b, rc, dev) between previous and current app_rdm
      3. For minor/micro: if increased, increase oarepo by same amount; if decreased, set to app_rdm value
      4. For a/b/rc/dev: set to the same value as in app_rdm
      5. If any field changed, set ordinal to 1; otherwise increment ordinal

    - If no local version exists:
      1. Increment micro
      2. Set a/b/rc/dev fields to match app_rdm
      3. Set ordinal to 1

    Args:
        oarepo_version: Current oarepo version (may include local version)
        app_rdm_version: Target app-rdm version

    Returns:
        New oarepo version with updated local version
    """
    # Parse local version if it exists
    local_info = parse_local_rdm_version(oarepo_version.local or "")

    major = oarepo_version.major
    minor = oarepo_version.minor
    micro = oarepo_version.micro
    new_pre = oarepo_version.pre
    new_dev = oarepo_version.dev

    if local_info:
        # Has local version with rdm tracking
        ordinal, prev_rdm_version = local_info

        # Track if anything has changed
        has_changes = False

        # Compare previous rdm version with current app_rdm_version
        # Check what changed and propagate those changes

        # Check minor version change
        if app_rdm_version.minor > prev_rdm_version.minor:
            # Minor increased - increase oarepo by same amount
            minor += app_rdm_version.minor - prev_rdm_version.minor
            has_changes = True
        elif app_rdm_version.minor < prev_rdm_version.minor:
            # Minor decreased - set to app_rdm value
            minor = app_rdm_version.minor
            has_changes = True

        # Check micro version change
        if app_rdm_version.micro > prev_rdm_version.micro:
            # Micro increased - increase oarepo by same amount
            micro += app_rdm_version.micro - prev_rdm_version.micro
            has_changes = True
        elif app_rdm_version.micro < prev_rdm_version.micro:
            # Micro decreased - set to app_rdm value
            micro = app_rdm_version.micro
            has_changes = True

        # Handle pre-release (a/b/rc) independently
        app_pre = app_rdm_version.pre

        if app_pre is not None:
            # App has pre-release - set oarepo to match
            if new_pre != app_pre:
                has_changes = True
            new_pre = app_pre
        else:
            # App doesn't have pre-release - remove from oarepo if present
            if new_pre is not None:
                has_changes = True
            new_pre = None

        # Handle dev independently
        app_dev = app_rdm_version.dev

        if app_dev is not None:
            # App has dev - set oarepo to match
            if new_dev != app_dev:
                has_changes = True
            new_dev = app_dev
        else:
            # App doesn't have dev - remove from oarepo if present
            if new_dev is not None:
                has_changes = True
            new_dev = None

        # Set ordinal based on whether anything changed
        if has_changes:
            new_ordinal = 1
        else:
            new_ordinal = ordinal + 1
    else:
        # No local version - increment micro and match app_rdm state
        micro += 1

        # Handle pre-release independently
        new_pre = app_rdm_version.pre

        # Handle dev independently
        new_dev = app_rdm_version.dev

        new_ordinal = 1

    # Build new version
    new_version = cast(
        Version,
        replace(
            oarepo_version,
            release=(major, minor, micro),
            pre=new_pre,
            dev=new_dev,
            local=f"{new_ordinal}.rdm.{str(app_rdm_version)}",
        ),  # type: ignore[type-var]
    )

    return new_version
