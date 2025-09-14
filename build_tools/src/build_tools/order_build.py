#
# Given the invenio-forks.json file (described at select_forks_from_zenodo_release.py),
# enrich the file with matrices of packages to be built in the order that respects
# dependencies. For each package:
#
# install it from the github repo (in a temporary venv)
# finds the dependencies that are also in the invenio-forks.json file
# creates a build matrix for the package and its dependencies
#
# The invneio-forks.json will be added a new element, 'build', that will contain
# step0 - stepN elements, each containing a list of packages to be built
# in that step. The steps are ordered so that dependencies are built before
# the packages that need them.
#
# For each package, we will also add the dependencies section with the list of
# "name==version" strings of the dependencies to CESNET forks of the packages.
#
import json
import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from build_tools.utils.git import clone_repository
from build_tools.utils.invenio import is_invenio_package
from build_tools.utils.pip import parse_pip_freeze

app = typer.Typer()


@app.command()
def main(
    invenio_forks_file: Annotated[
        str, typer.Argument(help="Path to the invenio-forks.json file")
    ],
    build_steps_file: Annotated[
        str, typer.Argument(help="Path to the output file for build steps")
    ],
):
    json_data = json.loads(Path(invenio_forks_file).read_text())

    python = os.environ.get("PYTHON_VERSION", "3.13")

    for package in json_data["packages"]:
        package_repository = package["repository_url"]
        package_commit = package["commit"]
        with clone_repository(package_repository, package_commit) as tmpdir:

            subprocess.check_call(
                ["uv", "venv", "--seed", "--python", python, ".venv"],
                cwd=tmpdir,
            )

            subprocess.check_call(
                [
                    "uv",
                    "pip",
                    "install",
                    "-p",
                    "./.venv/bin/python",
                    "-e",
                    ".[tests,opensearch2,s3]",
                ],
                cwd=tmpdir,
            )
            dependency_lines = subprocess.check_output(
                [
                    "uv",
                    "pip",
                    "freeze",
                    "-p",
                    "./.venv/bin/python",
                ],
                cwd=tmpdir,
                text=True,
            )

            dependencies_on_invenio_packages = [
                pkg
                for pkg in parse_pip_freeze(dependency_lines)
                if is_invenio_package(pkg.name)
            ]

            package["cesnet_dependencies"] = [
                dep.name for dep in dependencies_on_invenio_packages
            ]

    Path(invenio_forks_file).write_text(json.dumps(json_data, indent=2))

    built_package_names = set()
    dependencies: dict[str, set[str]] = {}

    for pkg in json_data["packages"]:
        built_package_names.add(pkg["name"])
        dependencies[pkg["name"]] = set()

    # reversed dependencies
    for pkg in json_data["packages"]:
        for dep in pkg.get("cesnet_dependencies", []):
            print(f"Package {pkg['name']} depends on {dep}")
            if dep in dependencies:
                dependencies[dep].add(pkg["name"])

    # now we have dependencies, we can create the build matrix
    build_steps = [pkg["name"] for pkg in json_data["packages"]]

    json_data["build"] = build_steps

    # index the packages by name
    json_data["pkg_index"] = {pkg["name"]: pkg for pkg in json_data["packages"]}

    # prune dependencies to only those that are in the forks
    for pkg in json_data["packages"]:
        if "cesnet_dependencies" in pkg:
            pkg["cesnet_dependencies"] = [
                f"{dep}=={json_data['pkg_index'][dep]['cesnet_version']}"
                for dep in pkg["cesnet_dependencies"]
                if dep in json_data["pkg_index"]
            ]
    Path(invenio_forks_file).write_text(json.dumps(json_data, indent=2))
    Path(build_steps_file).write_text(json.dumps(build_steps))


if __name__ == "__main__":
    app()
