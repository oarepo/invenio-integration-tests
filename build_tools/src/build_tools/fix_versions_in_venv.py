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


def fix_versions(rdm_requirements_file: Path):
    actual_packages = load_freeze_from_venv()
    rdm_packages = load_freeze_from_file(rdm_requirements_file)

    packages_to_update: list[str] = []

    for pkg_name, pkg_version in actual_packages.items():
        if pkg_name not in rdm_packages or rdm_packages[pkg_name] == pkg_version:
            continue

        packages_to_update.append(f"{pkg_name}=={rdm_packages[pkg_name]}")

    if packages_to_update:
        print("Updating packages to be in sync with actual RDM deps:")
        for pkg in packages_to_update:
            print(f"  {pkg}")
        subprocess.check_call(["uv", "pip", "install", *packages_to_update])
    else:
        print("All packages are in sync with RDM deps.")


if __name__ == "__main__":
    fix_versions(Path(sys.argv[1]))
