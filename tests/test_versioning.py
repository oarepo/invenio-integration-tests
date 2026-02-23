"""Tests for version propagation logic."""

from packaging.version import Version

from invenio_integration_tests.versioning import (
    parse_local_rdm_version,
    propagate_version,
)

# Tests for version.pre attribute


def test_get_pre_release_info_alpha():
    """Test getting pre-release info for alpha version."""
    version = Version("1.2.3a0")
    assert version.pre == ("a", 0)


def test_get_pre_release_info_alpha_incremented():
    """Test getting pre-release info for incremented alpha version."""
    version = Version("1.2.3a3")
    assert version.pre == ("a", 3)


def test_get_pre_release_info_beta():
    """Test getting pre-release info for beta version."""
    version = Version("1.2.3b0")
    assert version.pre == ("b", 0)


def test_get_pre_release_info_beta_incremented():
    """Test getting pre-release info for incremented beta version."""
    version = Version("1.2.3b2")
    assert version.pre == ("b", 2)


def test_get_pre_release_info_rc():
    """Test getting pre-release info for rc version."""
    version = Version("1.2.3rc0")
    assert version.pre == ("rc", 0)


def test_get_pre_release_info_rc_incremented():
    """Test getting pre-release info for incremented rc version."""
    version = Version("1.2.3rc1")
    assert version.pre == ("rc", 1)


def test_get_pre_release_info_published():
    """Test getting pre-release info for published version."""
    version = Version("1.2.3")
    assert version.pre is None


def test_get_pre_release_info_dev_only():
    """Test getting pre-release info for dev-only version."""
    version = Version("1.2.3.dev0")
    assert version.pre is None


# Tests for version.dev attribute


def test_get_dev_info_dev():
    """Test getting dev info for dev version."""
    version = Version("1.2.3.dev0")
    assert version.dev == 0


def test_get_dev_info_dev_incremented():
    """Test getting dev info for incremented dev version."""
    version = Version("1.2.3.dev5")
    assert version.dev == 5


def test_get_dev_info_published():
    """Test getting dev info for published version."""
    version = Version("1.2.3")
    assert version.dev is None


def test_get_dev_info_alpha_only():
    """Test getting dev info for alpha-only version."""
    version = Version("1.2.3a0")
    assert version.dev is None


# Tests for parse_local_rdm_version


def test_parse_local_rdm_version_valid():
    """Test parsing valid local rdm version."""
    ordinal, rdm_version = parse_local_rdm_version("1.rdm.12.0.0")
    assert ordinal == 1
    assert str(rdm_version) == "12.0.0"


def test_parse_local_rdm_version_valid_with_dev():
    """Test parsing valid local rdm version with dev."""
    ordinal, rdm_version = parse_local_rdm_version("5.rdm.12.0.0.dev2")
    assert ordinal == 5
    assert str(rdm_version) == "12.0.0.dev2"


def test_parse_local_rdm_version_valid_with_alpha():
    """Test parsing valid local rdm version with alpha."""
    ordinal, rdm_version = parse_local_rdm_version("2.rdm.12.0.0a1")
    assert ordinal == 2
    assert str(rdm_version) == "12.0.0a1"


def test_parse_local_rdm_version_invalid_format():
    """Test parsing invalid format returns None."""
    result = parse_local_rdm_version("invalid")
    assert result is None


def test_parse_local_rdm_version_empty():
    """Test parsing empty string returns None."""
    result = parse_local_rdm_version("")
    assert result is None


def test_parse_local_rdm_version_none():
    """Test parsing None returns None."""
    result = parse_local_rdm_version(None)
    assert result is None


# Tests for propagate_version - First time (no local version)


def test_propagate_first_time_published():
    """Test first propagation with published app_rdm increments micro and sets ordinal to 1."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4+1.rdm.12.0.0"


def test_propagate_first_time_dev():
    """Test first propagation with dev app_rdm increments micro and adds dev."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0.dev2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4.dev2+1.rdm.12.0.0.dev2"


def test_propagate_first_time_alpha():
    """Test first propagation with alpha app_rdm increments micro and adds alpha."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0a1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4a1+1.rdm.12.0.0a1"


def test_propagate_first_time_beta():
    """Test first propagation with beta app_rdm increments micro and adds beta."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0b0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4b0+1.rdm.12.0.0b0"


def test_propagate_first_time_rc():
    """Test first propagation with rc app_rdm increments micro and adds rc."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0rc1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4rc1+1.rdm.12.0.0rc1"


# Tests for propagate_version - Incremental updates (has local version)


def test_propagate_with_local_no_change():
    """Test propagation when app_rdm hasn't changed - just increment ordinal."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+2.rdm.12.0.0"


def test_propagate_with_local_micro_incremented():
    """Test propagation when app_rdm micro is incremented."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4+1.rdm.12.0.1"


def test_propagate_with_local_minor_incremented():
    """Test propagation when app_rdm minor is incremented."""
    oarepo = Version("1.2.3+1.rdm.12.0.5")
    app_rdm = Version("12.1.0")
    result = propagate_version(oarepo, app_rdm)
    # Minor increased by 1, so oarepo minor increases by 1 (2->3)
    # Micro decreased from 5 to 0, so oarepo micro set to 0
    assert str(result) == "1.3.0+1.rdm.12.1.0"


def test_propagate_with_local_dev_incremented():
    """Test propagation when app_rdm dev counter is incremented."""
    oarepo = Version("1.2.3.dev2+1.rdm.12.0.0.dev1")
    app_rdm = Version("12.0.0.dev3")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3.dev3+1.rdm.12.0.0.dev3"


def test_propagate_with_local_alpha_incremented():
    """Test propagation when app_rdm alpha counter is incremented."""
    oarepo = Version("1.2.3a0+1.rdm.12.0.0a0")
    app_rdm = Version("12.0.0a2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3a2+1.rdm.12.0.0a2"


def test_propagate_with_local_beta_incremented():
    """Test propagation when app_rdm beta counter is incremented."""
    oarepo = Version("1.2.3b1+1.rdm.12.0.0b0")
    app_rdm = Version("12.0.0b2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3b2+1.rdm.12.0.0b2"


def test_propagate_with_local_rc_incremented():
    """Test propagation when app_rdm rc counter is incremented."""
    oarepo = Version("1.2.3rc0+1.rdm.12.0.0rc0")
    app_rdm = Version("12.0.0rc1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc1+1.rdm.12.0.0rc1"


# Tests for fields appearing


def test_propagate_published_to_dev():
    """Test propagation when dev appears in app_rdm."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0.dev0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3.dev0+1.rdm.12.0.0.dev0"


def test_propagate_published_to_alpha():
    """Test propagation when alpha appears in app_rdm."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0a1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3a1+1.rdm.12.0.0a1"


def test_propagate_published_to_beta():
    """Test propagation when beta appears in app_rdm."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0b0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3b0+1.rdm.12.0.0b0"


def test_propagate_published_to_rc():
    """Test propagation when rc appears in app_rdm."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0rc2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc2+1.rdm.12.0.0rc2"


# Tests for fields disappearing


def test_propagate_dev_to_published():
    """Test propagation when dev disappears in app_rdm."""
    oarepo = Version("1.2.3.dev5+1.rdm.12.0.0.dev2")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+1.rdm.12.0.0"


def test_propagate_alpha_to_published():
    """Test propagation when alpha disappears in app_rdm."""
    oarepo = Version("1.2.3a2+1.rdm.12.0.0a1")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+1.rdm.12.0.0"


def test_propagate_beta_to_published():
    """Test propagation when beta disappears in app_rdm."""
    oarepo = Version("1.2.3b0+1.rdm.12.0.0b0")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+1.rdm.12.0.0"


def test_propagate_rc_to_published():
    """Test propagation when rc disappears in app_rdm."""
    oarepo = Version("1.2.3rc3+1.rdm.12.0.0rc1")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+1.rdm.12.0.0"


# Tests for field type changes


def test_propagate_dev_to_alpha():
    """Test propagation when field changes from dev to alpha."""
    oarepo = Version("1.2.3.dev1+1.rdm.12.0.0.dev0")
    app_rdm = Version("12.0.0a0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3a0+1.rdm.12.0.0a0"


def test_propagate_alpha_to_beta():
    """Test propagation when field changes from alpha to beta."""
    oarepo = Version("1.2.3a2+1.rdm.12.0.0a1")
    app_rdm = Version("12.0.0b0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3b0+1.rdm.12.0.0b0"


def test_propagate_beta_to_rc():
    """Test propagation when field changes from beta to rc."""
    oarepo = Version("1.2.3b5+1.rdm.12.0.0b3")
    app_rdm = Version("12.0.0rc0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc0+1.rdm.12.0.0rc0"


def test_propagate_alpha_to_dev():
    """Test propagation when field changes from alpha to dev."""
    oarepo = Version("1.2.3a1+1.rdm.12.0.0a0")
    app_rdm = Version("12.0.0.dev1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3.dev1+1.rdm.12.0.0.dev1"


# Complex scenarios


def test_propagate_micro_and_dev_incremented():
    """Test when both micro and dev are incremented."""
    oarepo = Version("1.2.3.dev1+1.rdm.12.0.0.dev0")
    app_rdm = Version("12.0.1.dev2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4.dev2+1.rdm.12.0.1.dev2"


def test_propagate_ordinal_increments():
    """Test that ordinal increments on each propagation."""
    oarepo = Version("1.2.3+5.rdm.12.0.0")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+6.rdm.12.0.0"


def test_propagate_preserves_major_minor():
    """Test that oarepo major and minor are preserved."""
    oarepo = Version("5.7.9+1.rdm.12.0.0")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert result.major == 5
    assert result.minor == 7


# Tests for combined pre-release and dev versions


def test_get_pre_release_info_with_dev():
    """Test getting pre-release info when version also has dev."""
    version = Version("1.2.3rc0.dev1")
    assert version.pre == ("rc", 0)
    assert version.dev == 1


def test_propagate_first_time_rc_with_dev():
    """Test first propagation with rc+dev app_rdm."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0rc0.dev1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4rc0.dev1+1.rdm.12.0.0rc0.dev1"


def test_propagate_first_time_alpha_with_dev():
    """Test first propagation with alpha+dev app_rdm."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0a1.dev3")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4a1.dev3+1.rdm.12.0.0a1.dev3"


def test_propagate_first_time_beta_with_dev():
    """Test first propagation with beta+dev app_rdm."""
    oarepo = Version("1.2.3")
    app_rdm = Version("12.0.0b2.dev0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4b2.dev0+1.rdm.12.0.0b2.dev0"


def test_propagate_rc_dev_to_rc_dev():
    """Test propagation when both rc and dev change."""
    oarepo = Version("1.2.3rc0.dev1+1.rdm.12.0.0rc0.dev0")
    app_rdm = Version("12.0.0rc1.dev2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc1.dev2+1.rdm.12.0.0rc1.dev2"


def test_propagate_rc_dev_to_rc_only():
    """Test propagation when dev is removed but rc remains."""
    oarepo = Version("1.2.3rc0.dev1+1.rdm.12.0.0rc0.dev1")
    app_rdm = Version("12.0.0rc0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc0+1.rdm.12.0.0rc0"


def test_propagate_rc_only_to_rc_dev():
    """Test propagation when dev is added to existing rc."""
    oarepo = Version("1.2.3rc0+1.rdm.12.0.0rc0")
    app_rdm = Version("12.0.0rc0.dev1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc0.dev1+1.rdm.12.0.0rc0.dev1"


def test_propagate_published_to_alpha_dev():
    """Test propagation from published to alpha+dev."""
    oarepo = Version("1.2.3+1.rdm.12.0.0")
    app_rdm = Version("12.0.0a0.dev0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3a0.dev0+1.rdm.12.0.0a0.dev0"


def test_propagate_alpha_dev_to_published():
    """Test propagation from alpha+dev to published."""
    oarepo = Version("1.2.3a1.dev2+1.rdm.12.0.0a1.dev2")
    app_rdm = Version("12.0.0")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3+1.rdm.12.0.0"


def test_propagate_alpha_dev_to_beta_dev():
    """Test propagation from alpha+dev to beta+dev."""
    oarepo = Version("1.2.3a0.dev1+1.rdm.12.0.0a0.dev1")
    app_rdm = Version("12.0.0b0.dev2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3b0.dev2+1.rdm.12.0.0b0.dev2"


def test_propagate_rc_dev_no_change():
    """Test propagation when rc+dev doesn't change - ordinal increments."""
    oarepo = Version("1.2.3rc1.dev2+5.rdm.12.0.0rc1.dev2")
    app_rdm = Version("12.0.0rc1.dev2")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.3rc1.dev2+6.rdm.12.0.0rc1.dev2"


def test_propagate_micro_with_rc_dev_incremented():
    """Test when micro, rc, and dev all change."""
    oarepo = Version("1.2.3rc0.dev0+1.rdm.12.0.0rc0.dev0")
    app_rdm = Version("12.0.1rc1.dev1")
    result = propagate_version(oarepo, app_rdm)
    assert str(result) == "1.2.4rc1.dev1+1.rdm.12.0.1rc1.dev1"
