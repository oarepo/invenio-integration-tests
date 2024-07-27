import dataclasses
from typing import Dict, Set

import click
import toml
from requirements.parser import parse as parse_requirements, Requirement


@click.command()
@click.argument("requirements_path", type=click.Path(exists=True), required=True)
@click.argument("test_requirements_path", type=click.Path(exists=True), required=True)
@click.argument("pyproject_toml_path", type=click.Path(exists=True), required=True)
def main(
    requirements_path,
    test_requirements_path,
    pyproject_toml_path,
):
    """
    Merge requirements to pyproject.toml
    """

    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

    normal_requirements = []
    rdm_requirements = []
    test_requirements = []
    seen_packages = set()

    with open(requirements_path, "r") as f:
        requirements = parse_requirements(f.read())
        for req in requirements:
            if req.name in seen_packages:
                continue
            if req.name in ('invenio-app-rdm', 'invenio-rdm-records'):
                rdm_requirements.append(req)
            else:
                normal_requirements.append(req)
            seen_packages.add(req.name)

    with open(test_requirements_path, "r") as f:
        requirements = parse_requirements(f.read())
        for req in requirements:
            if req.name in seen_packages:
                continue
            test_requirements.append(req)
            seen_packages.add(req.name)

    pyproject_toml["project"]["dependencies"] = [
        req.line for req in normal_requirements
    ]
    pyproject_toml["project"]["optional-dependencies"] = {
        "rdm": [req.line for req in rdm_requirements],
        "test": [req.line for req in test_requirements],
        "tests": [req.line for req in test_requirements],
        "dev": [req.line for req in test_requirements],
        "devs": [req.line for req in test_requirements],
    }

    encoder = toml.TomlArraySeparatorEncoder(separator=",\n    ")
    with open(pyproject_toml_path, "w") as f:
        toml.dump(pyproject_toml, f, encoder=encoder)

    click.secho(toml.dumps(pyproject_toml, encoder=encoder), fg="green")


if __name__ == "__main__":
    main()
