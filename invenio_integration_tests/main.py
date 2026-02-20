import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import click
from invenio_testrig.config import load_config
from invenio_testrig.utils import extra_data
from packaging.version import Version

from .pypi import GitLabPyPIClient, PyPIClient

CESNET_GITLAB_PYPI_URL = os.environ.get(
    "CESNET_GITLAB_PYPI_URL",
    "https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi",
)
EPOQUE_TAG = "v1:"


@click.group()
def cli():
    """Invenio Integration Tests CLI."""
    pass


@cli.command("setup")
@click.argument(
    "input_config", type=click.Path(path_type=Path, resolve_path=True, exists=True)
)
@click.argument(
    "preprocessed_config", type=click.Path(path_type=Path, resolve_path=True)
)
def setup(input_config: Path, preprocessed_config: Path):
    """Preprocess the input configuration and save it to the preprocessed configuration path."""
    import yaml

    with input_config.open() as f:
        config = yaml.safe_load(f)

    packages = config.pop("packages", [])
    supported_invenio_version = config.pop("invenio-version", None)
    patches = []
    entrypoints = {}
    for package_def in packages:
        package_name = package_def.pop("name")
        _unused_depends = package_def.pop("depends", [])
        _unused_dependencies = package_def.pop("dependencies", [])
        _unused_tests = package_def.pop("tests", [])
        if not package_name:
            raise ValueError(
                f"Package definition must include a 'name' field, got {package_def}"
            )
        for feature in package_def.pop("features", []):
            if isinstance(feature, str):
                patches.append(feature)
                continue
            feature_name = feature.pop("name")
            feature_base = feature.pop("base")
            feature_org = feature.pop("org", "oarepo")
            feature_str = f"{feature_org}/{package_name}@{feature_name}[{feature_base}]"

            invenio_version = feature.pop("invenio-version", None)
            if invenio_version:
                feature_str += invenio_version

            patches.append(feature_str)
            assert not feature, f"Unexpected keys in feature definition: {feature}"

        package_entrypoints = package_def.pop("entrypoints", {})
        if package_entrypoints:
            entrypoints[package_name] = package_entrypoints

        assert not package_def, f"Unexpected keys in package definition: {package_def}"

    assert not config, f"Unexpected keys in configuration: {config}"

    with preprocessed_config.open("w") as f:
        json.dump(
            {
                "invenio-version": supported_invenio_version,
                "patches": patches,
                "entrypoints": entrypoints,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


@cli.command("upload-original")
@click.argument("workdir", type=click.Path(path_type=Path, resolve_path=True))
@click.option(
    "--package",
    help="Specify a single package to upload (in the format 'package_name' or 'package_name==version'). If not specified, all packages will be uploaded.",
)
def upload_original(workdir: Path, package: str | None):
    """Upload original packages to the package registry."""

    cesnet_pypi_client = GitLabPyPIClient(CESNET_GITLAB_PYPI_URL)
    pypi_client = PyPIClient("https://pypi.org/")

    config_path = workdir / "config.json"
    config = load_config(config_path)

    click.secho(f"🔍 Fetching packages from {CESNET_GITLAB_PYPI_URL}...", fg="cyan")
    packages = set(cesnet_pypi_client.list_packages())
    click.secho(f"✅ Found {len(packages)} packages:{", ".join(packages)}", fg="green")

    # add all patched packages to the set of packages to upload, we will check their versions later
    for pkg_name, pkg_info in config.tested_packages.items():
        if pkg_info.patches:
            packages.add(pkg_name)

    packages_to_upload: set[tuple[str, str]] = set()
    for pkg in packages:
        if package and pkg.lower() != package.lower():
            continue
        click.secho(f"📦 Fetching versions for package {pkg}...", fg="cyan")
        uploaded_packages = cesnet_pypi_client.get_package_versions(pkg)
        pypi_packages = pypi_client.get_package_versions(pkg)
        packages_to_upload.update(
            (pkg, version) for version in set(pypi_packages) - set(uploaded_packages)
        )

    click.secho(
        f"📤 {len(packages_to_upload)} packages to upload:\n{"\n".join(f"{pkg}=={version}" for pkg, version in packages_to_upload)}",
        fg="yellow",
    )

    # for each package to upload, we will use pypi to download it to a temporary directory, and then upload it to the cesnet pypi using twine
    for pkg, version in packages_to_upload:
        with tempfile.TemporaryDirectory() as tmpdir:
            click.secho(f"⬇️  Downloading {pkg}=={version} from PyPI...", fg="blue")
            pypi_client.download_package(pkg, version, Path(tmpdir))
            downloaded_files = list(Path(tmpdir).glob("*"))
            click.secho(
                f"✅ Downloaded {len(downloaded_files)} distributions: {downloaded_files}",
                fg="green",
            )
            if downloaded_files:
                click.secho(
                    f"⬆️  Uploading {pkg}=={version} to CESNET pypi ...",
                    fg="magenta",
                )
                cesnet_pypi_client.upload_packages(downloaded_files)


@cli.command("find-distributions")
@click.argument("workdir", type=click.Path(path_type=Path, resolve_path=True))
def find_distributions(workdir: Path):
    """Find distributions for the patched packages and check if they match the expected patch info.

    The patched distributions at CESNET gitlab registry are always in the format:
    <base_version>+oarepo.ordinal_starting with 1.<hash_of_patch_info>
    """
    config_path = workdir / "config.json"
    config = load_config(config_path)
    cesnet_pypi_client = GitLabPyPIClient(CESNET_GITLAB_PYPI_URL)

    found_distributions: dict[str, Any] = {}

    for pkg_name, pkg_info in config.tested_packages.items():
        if not pkg_info.patches:
            continue
        pkg_patch_info = load_patch_info(
            find_patch_info_file(workdir / "cloned_repos" / "patched" / pkg_name)
        )
        patch_info_hash_value = hash_patch_info(pkg_patch_info)

        click.secho(
            f"📦 Looking for distributions for package {pkg_name}...", fg="cyan"
        )
        version = pkg_info.reference.actual_version
        if version is None:
            click.secho(
                f"⚠️  Package {pkg_name} does not have an actual version resolved, skipping...",
                fg="red",
            )
            continue
        # get a list of all versions of the package on cesnet_pypi that match the version
        # (versions with the same base version and a local oarepo identifier)
        uploaded_versions = [
            Version(v) for v in cesnet_pypi_client.get_package_versions(pkg_name)
        ]

        # the version can have .devN and .postN as well. We want to filter uploaded versions
        # to find those with the same base version and a "+oarepo.<nnn>" local version suffix
        matching_uploaded_versions = [
            v for v in uploaded_versions if cesnet_uploaded_version_of(v, version)
        ]

        # for each matching version, download it, unpack it, extract the patch info,
        # and check if it matches the current package's patch info
        pkg_rec = {
            "version": version,
            "hash": patch_info_hash_value,
            "uploaded_count": len(matching_uploaded_versions),
            "match": None,
        }
        click.secho(
            f"🔍 Found {len(matching_uploaded_versions)} matching uploaded versions for {pkg_name}",
            fg="cyan",
        )
        for potential_match in matching_uploaded_versions:
            if not potential_match.local:
                continue
            split_local = potential_match.local.split(".")
            if len(split_local) < 3:
                click.secho(
                    f"ℹ️  Uploaded version {potential_match} does not have the expected local version format, skipping...",
                    fg="cyan",
                )
                continue
            potential_hash = split_local[2]
            if potential_hash != patch_info_hash_value:
                click.secho(
                    f"ℹ️  Uploaded version {potential_match} has a different patch info hash ({potential_hash}) than expected ({patch_info_hash_value}), skipping...",
                    fg="cyan",
                )
                continue
            pkg_rec["match"] = str(potential_match)
            break
        found_distributions[pkg_name] = pkg_rec
    extra_data(config)["found_distributions"] = found_distributions
    config.save()


@cli.command("build-distributions")
@click.argument("workdir", type=click.Path(path_type=Path, resolve_path=True))
def build_distributions(workdir: Path):
    (workdir / "dist").mkdir(exist_ok=True)

    config = load_config(workdir / "config.json")
    for pkg_name, build_info in (
        extra_data(config).get("found_distributions", {}).items()
    ):
        if build_info.get("match"):
            click.secho(
                f"ℹ️  {pkg_name} with the correct version was already uploaded, skipping...",
                fg="cyan",
            )
            continue
        package_dir = workdir / "cloned_repos" / "patched" / pkg_name
        if not package_dir.is_dir():
            click.secho(
                f"⚠️  Package directory {package_dir} does not exist, skipping...",
                fg="red",
            )
            continue

        click.secho(f"📦 Building distributions for {pkg_name}...", fg="cyan")

        # Prepare version string with oarepo suffix
        hash_value = build_info["hash"]
        ordinal = build_info["uploaded_count"] + 1

        # Copy sources to temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_package_dir = Path(tmpdir) / pkg_name
            shutil.copytree(package_dir, tmp_package_dir)

            if not update_version_in_init(
                tmp_package_dir, pkg_name, ordinal, hash_value
            ):
                raise ValueError(
                    f"Could not update version in {tmp_package_dir / pkg_name / '__init__.py'}"
                )
            (workdir / "dist" / pkg_name).mkdir(exist_ok=True)
            subprocess.check_call(
                [
                    "uv",
                    "build",
                    "-o",
                    str(workdir / "dist" / pkg_name),
                ],
                cwd=tmp_package_dir,
            )


@cli.command("upload-distributions")
@click.argument("workdir", type=click.Path(path_type=Path, resolve_path=True))
def upload_distributions(workdir: Path):
    """Upload the contents of workdir/dist to the CESNET GitLab PyPI registry.

    Uploads each package separately (one twine call per package).
    """
    cesnet_pypi_client = GitLabPyPIClient(CESNET_GITLAB_PYPI_URL)
    dist_dir = workdir / "dist"
    if not dist_dir.is_dir():
        click.secho(
            f"⚠️  Distribution directory {dist_dir} does not exist, skipping...",
            fg="red",
        )
        return

    # Iterate through package subdirectories
    package_dirs = [d for d in dist_dir.iterdir() if d.is_dir()]
    if not package_dirs:
        click.secho(
            f"⚠️  No package directories found in {dist_dir}, skipping...", fg="red"
        )
        return

    for package_dir in package_dirs:
        pkg_name = package_dir.name
        package_files = list(package_dir.glob("*.tar.gz")) + list(
            package_dir.glob("*.whl")
        )

        if not package_files:
            click.secho(
                f"⚠️  No distribution files found for {pkg_name}, skipping...",
                fg="yellow",
            )
            continue

        click.secho(
            f"📤 Uploading {len(package_files)} distribution files for {pkg_name} to CESNET GitLab PyPI registry...",
            fg="magenta",
        )
        cesnet_pypi_client.upload_packages(package_files)


def update_version_in_init(
    package_dir: Path, pkg_name: str, ordinal: int, hash_value: str
) -> bool:
    """Update the __version__ variable in a package's __init__.py file."""
    pkg_file_part = pkg_name.replace("-", "_")
    init_file = package_dir / pkg_file_part / "__init__.py"
    content = init_file.read_text().splitlines()
    for idx, l in enumerate(content):
        if l.startswith("__version__"):
            # parse the actual version from the line
            version_str = l.split("=", 1)[1].strip().strip('"').strip("'")
            # add the local part
            version_str += f"+oarepo.{ordinal}.{hash_value}"
            print(version_str)
            content[idx] = f'__version__ = "{version_str}"'
            init_file.write_text("\n".join(content))
            return True
    return False


def check_uploaded_version_matches(
    pkg_name: str,
    potential_match: Version,
    version: str,
    patch_info_hash_value: str,
    cesnet_pypi_client: GitLabPyPIClient,
) -> bool:
    """Check if an uploaded version matches the expected patch info. To do it,
    expects that the uploaded version has the following format:
    +oarepo.<ordinal>.<hash_of_patch_info>
    """
    click.secho(
        f"🔍 Checking uploaded version {potential_match} against expected version {version}...",
        fg="yellow",
    )
    local_value = potential_match.local
    if not local_value or not local_value.startswith("oarepo."):
        return False

    #

    with tempfile.TemporaryDirectory() as tmpdir:
        cesnet_pypi_client.download_package(
            pkg_name, str(potential_match), Path(tmpdir)
        )
        downloaded_files = list(Path(tmpdir).glob("*"))
        if not downloaded_files:
            click.secho(
                f"⚠️  No files downloaded for {pkg_name}=={potential_match}, skipping...",
                fg="red",
            )
            return False
        # we expect only one file, but we will take the first one just in case
        distribution_file = downloaded_files[0]
        unpack_distribution_file(distribution_file, Path(tmpdir))
        potential_match_patch_info_path = find_patch_info_file(Path(tmpdir))
        if not potential_match_patch_info_path:
            click.secho(
                f"⚠️  No patch_info.py found in the distribution for {pkg_name}=={potential_match}, skipping...",
                fg="red",
            )
            return False
        potential_match_patch_info = load_patch_info(potential_match_patch_info_path)
        if patch_info_equal(pkg_patch_info, potential_match_patch_info):
            return True
        return False


def find_patch_info_file(search_path: Path) -> Path:
    """Look for the patch_info.py with Path's rglob, return the first one found, or None if not found."""
    for path in search_path.rglob("patch_info.py"):
        if path.is_file():
            return path
    raise FileNotFoundError(f"No patch_info.py found in {search_path}")


def load_patch_info(patch_info_path: Path):
    """Call the current python in subproces to run the patch_info.py and parse the output as json."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(patch_info_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def hash_patch_info(info) -> str:
    """Returns an sha256 hash of a normalized patch info."""

    def normalize(info):
        if isinstance(info, list):
            return sorted(
                [normalize(i) for i in info],
                key=lambda x: json.dumps(x, sort_keys=True),
            )
        if isinstance(info, dict):
            return {k: normalize(v) for k, v in info.items()}
        return str(info) if info is not None else None

    dump = EPOQUE_TAG + json.dumps(normalize(info), sort_keys=True)
    digest = hashlib.sha256(dump.encode()).digest()
    # convert the digest to [a-z0-9] alphabet and take the first 16 characters
    # to get a short but still reasonably unique identifier
    return base64.b32encode(digest).decode("ascii").lower().rstrip("=")[:16]


def unpack_distribution_file(distribution_file: Path, unpack_dir: Path):
    """Unpack a distribution file (wheel or source) to the specified directory."""
    if distribution_file.suffix == ".whl":
        shutil.unpack_archive(str(distribution_file), str(unpack_dir), "zip")
    elif distribution_file.suffix in [".tar.gz", ".zip"]:
        shutil.unpack_archive(str(distribution_file), str(unpack_dir))
    else:
        raise ValueError(f"Unsupported distribution file format: {distribution_file}")


def cesnet_uploaded_version_of(uploaded_version: Version, target_version: str) -> bool:
    """
    It is a cesnet uploaded version of the target version if it has the same fields.
    Additionally, we require a local version in the form of oarepo.<nnn> to distinguish
    it from the original version. This allows us to have multiple uploaded versions of the same original version, which is useful for testing multiple patches against the same original version without having to wait for the next release of the original package
    """
    target = Version(target_version)

    # Check if base versions match (major.minor.patch)
    if (
        uploaded_version.base_version != target.base_version
        or uploaded_version.pre != target.pre
        or uploaded_version.post != target.post
    ):
        return False

    return (uploaded_version.local or "").startswith("oarepo.")


if __name__ == "__main__":
    cli()
