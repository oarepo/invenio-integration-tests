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

We also fill in the actual version, repository, tag, commits_from_tag and checksum
fields for each package. For features, we compute only the checksum.

The version of the package inside CESNET github repo is in the form X.Y.Z.T.dev1,
where XYZ are the version of the package from invenio and T is a number
taken from the full checksum mod 10000. We do not need ordering of versions here
as we always generate the 'oarepo' package and that contains direct references to the
exact versions of the packages stored in CESNET pypi.
"""

import json
import re
import typing
from hashlib import md5
from pathlib import Path
from typing import Any

import typer

from build_tools.utils.git import clone_repository, get_commit, get_nearest_version_tag
from build_tools.utils.invenio import invenio2repo, is_invenio_package
from build_tools.utils.pip import ParsedVersion, check_pkg_version, parse_pip_freeze

app = typer.Typer()


@app.command()
def select_forks_from_zenodo_freeze(
    forks_json_path: Path, output_json_path: Path, initial_requirements_path: Path
):
    # load the forks json file and package versions from the virtualenv
    json_data = json.loads(forks_json_path.read_text())
    original_requirements = parse_requirements_output(
        initial_requirements_path.read_text()
    )

    # for each package, keep only those patches that match the actual version
    json_data["packages"] = [
        prune_invenio_version_mismatches(pkg, pkg["name"], original_requirements)
        for pkg in json_data.get("packages", [])
    ]
    json_data["packages"] = [pkg for pkg in json_data["packages"] if pkg is not None]

    for pkg in json_data["packages"]:
        pkg["package"] = pkg["name"]
        pkg["version"] = original_requirements[pkg["name"].lower()].version

        # repository url looks like https://github.com/inveniosoftware/invenio-xyz[.git]
        pkg["repository_url"] = original_requirements[pkg["name"].lower()].github_repo

        # get the org/name from the url
        pkg["repository"] = re.sub(
            r"^https://github\.com/(.+?)(?:\.git)?$", r"\1", pkg["repository_url"]
        )
        pkg["oarepo_repository"] = pkg["repository"].replace(
            "inveniosoftware", "oarepo"
        )

        pkg["tag"] = original_requirements[pkg["name"].lower()].github_tag
        pkg["commit"] = original_requirements[pkg["name"].lower()].commit

    # compute checksums of features
    for pkg in json_data["packages"]:
        for feature in pkg.get("features", []):
            feature["commit"] = get_tag_version(
                pkg["name"],
                f"https://github.com/oarepo/{pkg['name']}",
                f"oarepo-feature-{feature['name']}",
                f"https://github.com/inveniosoftware/{pkg['name']}",
            ).commit

    # compute checksum of the whole package
    for pkg in json_data["packages"]:
        checksum_list = [pkg["commit"]]
        for feature in pkg.get("features", []):
            checksum_list.append(feature["commit"])

        print(f"Computing full checksum of {pkg['name']} from {checksum_list}")
        pkg["full_checksum"] = md5("".join(checksum_list).encode("utf-8")).hexdigest()
        print(f"Full checksum of {pkg['name']} is {pkg['full_checksum']}")

        # version of the package inside CESNET github repo is in the form X.Y.Z.T,
        # where XYZ are the version of the package from invenio and T is a number
        # taken from the full checksum mod 1000000. We take care of any pre/post/dev/a/b releases
        # and also add '0' if the version looks like X.Y

        # split on non-numeric characters, keeping those characters as well
        version_part_and_suffix = re.split("([^0-9.])", pkg["version"])
        main_version = version_part_and_suffix[0]
        suffix = "".join(version_part_and_suffix[1:])  # including the separator

        main_version_parts = main_version.split(".")
        while len(main_version_parts) < 3:
            main_version_parts.append("0")
        main_version_parts.append(str(int(pkg["full_checksum"], 16) % 100000000))
        if (
            not pkg.get("features")
            and not pkg.get("entrypoints")
            and not pkg.get("dependencies")
        ):
            # if there are no features and no frozen packages, we can use the exact version
            pkg["cesnet_version"] = pkg["version"]
        else:
            pkg["cesnet_version"] = ".".join(main_version_parts) + suffix

    print(json_data)
    # and dump
    output_json_path.write_text(json.dumps(json_data, indent=2))


@typing.no_type_check
def prune_invenio_version_mismatches(
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
            processed_item = prune_invenio_version_mismatches(
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
            el[k] = prune_invenio_version_mismatches(v, package_name, actual_packages)
    return el


def parse_requirements_output(output: str) -> dict[str, ParsedVersion]:
    ret = {}
    for pv in parse_pip_freeze(output):
        if is_invenio_package(pv.name):
            github_repo = pv.github_repo or invenio2repo(pv.name)
            github_tag = pv.github_tag or f"v{pv.version}"
            ret[pv.name] = get_tag_version(pv.name, github_repo, github_tag)
        else:
            # we will never patch non-invenio packages, so just store the version
            ret[pv.name] = pv
    return ret


def get_tag_version(
    name: str, url: str, tag: str | None, upstream: str | None = None
) -> ParsedVersion:
    print(f"Getting version and commit for {url} {tag}")
    with clone_repository(url, tag, upstream) as tmpdir:
        nearest_version = get_nearest_version_tag(tmpdir)
        commit = get_commit(tmpdir)
        return ParsedVersion(name, nearest_version[1:], url, tag, commit)


if __name__ == "__main__":
    app()
