import json
from pathlib import Path
from pprint import pprint
from typing import Annotated

import toml
import typer

app = typer.Typer()


@app.command()
def main(
    oarepo_version: str,
    requirements_json_file: Annotated[
        Path, typer.Argument(help="Path to the rdm_requirements.json file")
    ],
    forked_packages_json_file: Annotated[
        Path, typer.Argument(help="Path to the forked_packages.json file")
    ],
    extra_requirements_path: Annotated[
        Path, typer.Argument(help="Path to the file with extra requirements")
    ],
    pyproject_toml_path: Annotated[
        Path, typer.Argument(help="Path to the output file")
    ],
):
    normal_requirements = json.loads(requirements_json_file.read_text())
    forked_packages = json.loads(forked_packages_json_file.read_text())
    extra_requirements = json.loads(extra_requirements_path.read_text())

    forked_packages = {
        x["package"]: x["cesnet_version"] for x in forked_packages["packages"]
    }

    common_versions = {r["name"]: r["version"] for r in normal_requirements}

    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

    pprint(normal_requirements)
    pprint(forked_packages)

    dependencies = []
    rdm_dependencies = []
    test_dependencies = ["pytest-invenio"]

    rdm_packages = {
        "invenio-app-rdm",
        "invenio-rdm-records",
    }

    normal_requirements_dict = {}
    for r in normal_requirements:
        formatted, name = format_dependency(forked_packages, r["name"], common_versions)
        normal_requirements_dict[name] = formatted

        if name in rdm_packages:
            rdm_dependencies.append(formatted)
        else:
            dependencies.append(formatted)

    for pkg, version in extra_requirements.items():
        dependencies.append(f"{pkg}{version}")

    pyproject_toml["project"]["dependencies"] = dependencies

    pyproject_toml["project"]["optional-dependencies"] = {
        "rdm": rdm_dependencies,
        "test": test_dependencies,
        "tests": test_dependencies,
        "dev": test_dependencies,
        "devs": test_dependencies,
        "s3": [],  # backward compatibility, s3 is baked in the base image
    }

    encoder = toml.TomlArraySeparatorEncoder(separator=",\n    ")
    with open(pyproject_toml_path, "w") as f:
        toml.dump(pyproject_toml, f, encoder=encoder)

    print(toml.dumps(pyproject_toml, encoder=encoder))


def format_dependency(forked_packages, name, versions):
    version = versions[name]
    if name not in forked_packages:
        formatted = f"{name}=={version}"
    else:
        formatted = f"{name}=={forked_packages[name]}"
    return formatted, name


if __name__ == "__main__":
    app()
