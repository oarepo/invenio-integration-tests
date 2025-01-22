import json
import os
import subprocess
import sys
from pathlib import Path


def load_freeze_from_venv() -> dict[str, str]:
    output = subprocess.check_output(["uv", "pip", "freeze"], text=True)
    return {
        part.split("==", maxsplit=1)[0].lower(): part.split("==", maxsplit=1)[1]
        for part in output.split("\n")
        if part and "==" in part
    }


def load_freeze_from_file(path: Path) -> dict[str, str]:
    parts = [x.strip() for x in path.read_text().split("\n")]
    parts = [x for x in parts if x and "==" in x]
    return {
        part.split("==", maxsplit=1)[0].lower(): part.split("==", maxsplit=1)[1]
        for part in parts
    }


def fix_versions(rdm_requirements_file: Path, this_module_config_file: Path):
    actual_packages = load_freeze_from_venv()
    rdm_packages = load_freeze_from_file(rdm_requirements_file)

    packages_to_update: list[str] = []

    versions: dict[str, str] = {}

    for pkg_name, pkg_version in actual_packages.items():
        versions[pkg_name] = pkg_version
        if pkg_name not in rdm_packages or rdm_packages[pkg_name] == pkg_version:
            continue
        if pkg_name in ("importlib_metadata", "importlib-metadata"):
            # invenio-administration's mocks depend on the newer version of importlib_metadata
            continue
        packages_to_update.append(f"{pkg_name}=={rdm_packages[pkg_name]}")
        versions[pkg_name] = rdm_packages[pkg_name]

    if packages_to_update:
        print("Updating packages to be in sync with actual RDM deps:")
        for pkg in packages_to_update:
            print(f"  {pkg}")
        subprocess.check_call(["uv", "pip", "install", *packages_to_update])
    else:
        print("All packages are in sync with RDM deps.")

    pypi_url = os.environ["CESNET_PYPI_URL"]

    module_config = json.loads(this_module_config_file.read_text())
    for dependency in module_config.get("depends", []):
        depends_on = dependency["on"]
        # this module depends on a patched version of another module
        if depends_on in versions:
            version = versions[depends_on]
            if ".post" not in version:
                version += ".post1000000"
            print(f"Installing patched version of {depends_on} ({version})")
            subprocess.check_call(
                [
                    "uv",
                    "pip",
                    "install",
                    "-U",
                    "--extra-index-url",
                    pypi_url,
                    f"{depends_on}<={version}",
                ]
            )


if __name__ == "__main__":
    fix_versions(Path(sys.argv[1]), Path(sys.argv[2]))
