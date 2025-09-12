"""
This tools looks at the invenio-forks.json file passed as a cmdline argument
and compares it with the actual versions of the packages in zenodo freeze.

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
import re
import subprocess
import sys
import tempfile
import typing
from collections import namedtuple
from pathlib import Path
from typing import Any

ParsedVersion = namedtuple("package", ["version", "github_repo", "github_tag"])


def select_forks_by_venv(
    input_json_path: Path, output_json_path: Path, initial_requirements_path: Path
):
    # load the forks json file and package versions from the virtualenv
    json_data = json.loads(input_json_path.read_text())
    original_requirements = parse_requirements_output(
        initial_requirements_path.read_text()
    )

    # process each package
    json_data["packages"] = [
        remove_invenio_version_from_file(pkg, pkg["name"], original_requirements)
        for pkg in json_data.get("packages", [])
    ]
    json_data["packages"] = [pkg for pkg in json_data["packages"] if pkg is not None]
    for pkg in json_data["packages"]:
        pkg["package"] = pkg["name"]
        pkg["invenio_version"] = original_requirements[pkg["name"].lower()].version
        pkg["invenio_repository"] = original_requirements[
            pkg["name"].lower()
        ].github_repo
        pkg["invenio_tag"] = original_requirements[pkg["name"].lower()].github_tag
        pkg["version"] = pkg["invenio_version"]
    print(json_data)
    # and dump
    output_json_path.write_text(json.dumps(json_data, indent=2))


@typing.no_type_check
def remove_invenio_version_from_file(
    el: Any, package_name: str, actual_packages: dict[str, ParsedVersion]
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
            if package_name.lower() not in actual_packages or not check_pkg_version(
                actual_packages[package_name.lower()].version, el["invenio-version"]
            ):
                print("version mismatch, removing", el)
                return None
            el.pop("invenio-version", None)
        for k, v in el.items():
            el[k] = remove_invenio_version_from_file(v, package_name, actual_packages)
    return el


def parse_requirements_output(output: str) -> dict[str, ParsedVersion]:
    ret = {}
    for part in output.split("\n"):
        part = part.strip()
        if part.startswith("#") or not part:
            continue
        if ";" in part:
            part = part.split(";", maxsplit=1)[0].strip()
        if "==" in part:
            ret[part.split("==", maxsplit=1)[0].lower()] = ParsedVersion(
                part.split("==", maxsplit=1)[1], None, None
            )
        elif "@ git+" in part:
            # github dependence in the form of invenio-app-rdm @ git+https://github.com/inveniosoftware/invenio-app-rdm@eee215c4bc9b7b89ec4a7eb633d145aaab008a3b
            name, rest = part.split(" @ git+", maxsplit=1)
            if "@" in rest:
                url, tag = rest.split("@", maxsplit=1)
            else:
                url = rest
                tag = None
            if url.endswith(".git"):
                url = url[: -len(".git")]
            if url.startswith("git+"):
                url = url[5:]

            ret[name.lower()] = get_tag_version(url, tag)
    return ret


def get_tag_version(url: str, tag: str | None) -> ParsedVersion:
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_call(["git", "clone", url, tmpdir])
        if tag:
            subprocess.check_call(["git", "checkout", tag], cwd=tmpdir)

            # try to find out if there is a version tag that points to the current commit
            tag_names = [
                x.strip()
                for x in subprocess.check_output(
                    ["git", "tag", "--points-at", tag], cwd=tmpdir, text=True
                ).split("\n")
                if x.strip() and x.startswith("v")
            ]
            if tag_names:
                # there is an explicit version tag for this commit, use it
                return ParsedVersion(tag_names[0][1:], None, None)

        nearest_version = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"],
            cwd=tmpdir,
            text=True,
        ).strip()

        return ParsedVersion(nearest_version[1:], url, tag)


def extract_version(version_str: str) -> tuple[int, ...]:
    ret = []

    for part in version_str.split("."):
        res = (re.split("[a-z]", part))[0]

        if not res:
            continue

        ret.append(int(res))

    return tuple(ret)


def check_pkg_version(actual_pkg_version: str | None, fork_version: str) -> bool:
    if actual_pkg_version is None:
        return False

    fork_version_inequalities = fork_version.split(",")
    actual_pkg_version_tuple = extract_version(actual_pkg_version)
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
    select_forks_by_venv(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
