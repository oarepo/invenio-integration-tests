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


def load_freeze_from_venv() -> dict[str, str]:
    output = subprocess.check_output(["uv", "pip", "freeze"], text=True)
    return {
        part.split("==", maxsplit=1)[0].lower(): part.split("==", maxsplit=1)[1]
        for part in output.split("\n")
        if part and "==" in part
    }


def check_pkg_version(actual_pkg_version: str | None, fork_version: str) -> bool:
    if actual_pkg_version is None:
        return False

    fork_version_inequalities = fork_version.split(",")
    actual_pkg_version_tuple = tuple(int(x) for x in actual_pkg_version.split("."))
    for ineq in fork_version_inequalities:
        op = ""
        while ineq[0] in ["<", ">", "="]:
            op += ineq[0]
            ineq = ineq[1:]
        tested_version_tuple = tuple(int(x) for x in ineq.split("."))
        if op == "<":
            if actual_pkg_version_tuple >= tested_version_tuple:
                return False
        elif op == ">":
            if actual_pkg_version_tuple <= tested_version_tuple:
                return False
        elif op == "==":
            if actual_pkg_version_tuple != tested_version_tuple:
                return False
        elif op == ">=":
            if actual_pkg_version_tuple < tested_version_tuple:
                return False
        elif op == "<=":
            if actual_pkg_version_tuple > tested_version_tuple:
                return False
    return True


def install_frozen_dependencies(invenio_forks: Path):
    forks = json.loads(invenio_forks.read_text())
    fork_packages: list[Any] = forks.get("packages", [])
    actual_packages = load_freeze_from_venv()
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
                    f"Installing frozen dependencies for {pkg["name"]} @ {actual_pkg_version}"
                )
                print(frozen["packages"])
                subprocess.check_call(["pip", "install", *frozen["packages"]])
                print("After installation, the freeze is:")
                subprocess.call(["pip", "freeze"])


if __name__ == "__main__":
    install_frozen_dependencies(Path(sys.argv[1]))
