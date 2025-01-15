"""
Installs frozen packages from a json file.

Must be called from within the target virtual environment. Calls pip freeze,
for each of the forked packages, if there are any freezes, overrides the installed
version with the frozen one.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def install_frozen_dependencies(invenio_forks: Path):
    forks = json.loads(invenio_forks.read_text())
    fork_packages: list[Any] = forks.get("packages", [])
    actual_packages = load_freeze_from_venv()
    packages_to_install: list[str] = []
    for pkg in fork_packages:
        if "frozen" not in pkg:
            continue
        actual_pkg_version = actual_packages.get(pkg["name"].lower())
        for frozen in pkg["frozen"]:
            print(
                f"Checking if should apply frozen version for {pkg["name"]} @ {actual_pkg_version}"
            )
            invenio_version = frozen.get("invenio-version", None)
            print(
                "Versions of the package that should have the dependencies frozen: ",
                invenio_version,
            )

            if not invenio_version or check_pkg_version(
                actual_pkg_version, invenio_version
            ):
                print(
                    f"Collecting frozen dependencies for {pkg["name"]} @ {actual_pkg_version}"
                )
                print(frozen["packages"])
                packages_to_install.extend(frozen["packages"])

    if packages_to_install:
        subprocess.check_call(["uv", "pip", "install", *packages_to_install])
        print("After installation, the freeze is:")
        subprocess.call(["uv", "pip", "freeze"])


if __name__ == "__main__":
    install_frozen_dependencies(Path(sys.argv[1]))
