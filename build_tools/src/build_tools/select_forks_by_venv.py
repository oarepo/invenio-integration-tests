"""
This tools looks at the invenio-forks.json file passed as a cmdline argument
and compares it with the actual versions of the packages in the virtualenv.

It will select only those parts of the file that have the matching version
of the package.

Example:

<inside_venv>/bin/python select_forks_by_venv.py invenio-forks.json selected_forks.json

Input:

packages:
  - name: invenio-administration
    oarepo: 12
    features:
      - name: multiple-ui-changes
        base: v2.2.4
        invenio-version: "<2.2.6"
    frozen:
      - packages:
          - pytest-invenio<3.0.0

Output if the invenio-administration is installed with version 2.2.5:

packages:
  - name: invenio-administration
    oarepo: 12
    features:
      - name: multiple-ui-changes
        base: v2.2.4
    frozen:
      - packages:
          - pytest-invenio<3.0.0

Output if the inveio-administration is installed with version 2.2.6 or higher:

packages:
    - name: invenio-administration
      oarepo: 12
      features: []
      frozen:
      - packages:
        - pytest-invenio<3.0.0
"""

import json
import subprocess
import sys
import typing
from pathlib import Path
from typing import Any


def select_forks_by_venv(input_json_path: Path, output_json_path: Path):
    # load the forks json file and package versions from the virtualenv
    json_data = json.loads(input_json_path.read_text())
    actual_packages = load_freeze_from_venv()

    # process each package
    json_data["packages"] = [
        remove_invenio_version_from_file(pkg, pkg["name"], actual_packages)
        for pkg in json_data.get("packages", [])
    ]
    json_data["packages"] = [pkg for pkg in json_data["packages"] if pkg is not None]
    for pkg in json_data["packages"]:
        pkg["invenio_version"] = actual_packages.get(pkg["name"].lower())
    # and dump
    output_json_path.write_text(json.dumps(json_data, indent=2))


@typing.no_type_check
def remove_invenio_version_from_file(
    el: Any, package_name: str, actual_packages: dict[str, str]
) -> Any:
    """
    Recursively remove elements that contain invenio-version attribute with
    a version specifier that does not match the actual version of the package.
    """
    print(
        f"Processing {package_name} with {el}. Actual version: {actual_packages.get(package_name.lower())}"
    )
    if isinstance(el, list):
        for idx, item in enumerate(list(el)):
            processed_item = remove_invenio_version_from_file(
                item, package_name, actual_packages
            )
            el[idx] = processed_item
        el = [item for item in el if item is not None]
    elif isinstance(el, dict):
        if "invenio-version" in el:
            if not check_pkg_version(
                actual_packages.get(package_name.lower()), el["invenio-version"]
            ):
                print("version mismatch, removing", el)
                return None
            el.pop("invenio-version", None)
        for k, v in el.items():
            el[k] = remove_invenio_version_from_file(v, package_name, actual_packages)
    return el


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
        else:
            raise ValueError(f"Unknown operator {op}")
    return True


if __name__ == "__main__":
    select_forks_by_venv(Path(sys.argv[1]), Path(sys.argv[2]))
