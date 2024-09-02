import json
from importlib.metadata import version
from pathlib import Path
from pprint import pprint
from typing import Annotated
import toml
import semver

import typer

app = typer.Typer()

@app.command()
def main(oarepo_version: str,
        requirements_json_file: Annotated[Path, typer.Argument(help="Path to the rdm_requirements.json file")],
        test_requirements_json_file: Annotated[Path, typer.Argument(help="Path to the rdm_test_requirements.json file")],
        forked_packages_json_file: Annotated[Path, typer.Argument(help="Path to the forked_packages.json file")],
        pyproject_toml_path: Annotated[Path, typer.Argument(help="Path to the output file")],
        version_py_path: Annotated[Path, typer.Argument(help="Path to the version.py file")]):

    normal_requirements = json.loads(requirements_json_file.read_text())
    test_requirements = json.loads(test_requirements_json_file.read_text())
    forked_packages = json.loads(forked_packages_json_file.read_text())

    # a list of serialized json objects in fact to enable usage in github matrix
    forked_packages = [json.loads(x) for x in forked_packages]
    forked_packages = {x['package']: x['version'] for x in forked_packages}

    common_versions = {
        r['name']: r['version'] for r in normal_requirements
    }
    for r in test_requirements:
        name = r['name']
        version = r['version']
        if name not in common_versions:
            common_versions[name] = version
        elif common_versions[name] != version:
            print(f"Version conflict for {name}: {common_versions[name]} vs {version}")
            common_versions[name] = semver.min_ver(common_versions[name], version)


    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

    pprint(normal_requirements)
    pprint(test_requirements)
    pprint(forked_packages)

    dependencies = []
    rdm_dependencies = []
    test_dependencies = []

    rdm_packages = {
        'invenio-app-rdm',
        'invenio-rdm-records',
    }

    normal_requirements_dict = {}
    for r in normal_requirements:
        formatted, name = format_dependency(forked_packages, r['name'], common_versions)
        normal_requirements_dict[name] = formatted

        if name in rdm_packages:
            rdm_dependencies.append(formatted)
        else:
            dependencies.append(formatted)

    for r in test_requirements:
        if r['name'] in normal_requirements_dict:
            continue
        formatted, name = format_dependency(forked_packages, r['name'], common_versions)
        test_dependencies.append(formatted)


    pyproject_toml["project"]["dependencies"] = dependencies

    pyproject_toml["project"]["optional-dependencies"] = {
        "rdm": rdm_dependencies,
        "test": test_dependencies,
        "tests": test_dependencies,
        "dev": test_dependencies,
        "devs": test_dependencies,
        "s3": []  # backward compatibility, s3 is baked in the base image
    }

    # increment the version
    version = semver.Version.parse(pyproject_toml["project"]["version"])
    version = version.bump_patch()
    pyproject_toml["project"]["version"] = str(version)

    with open(version_py_path, "w") as f:
        f.write(f"""
# the first 3 numbers of version here must be the same as invenio version in setup.py
# if the version ends with a*, add this to the first 3 numbers
__version__ = "{version}"
""")

    encoder = toml.TomlArraySeparatorEncoder(separator=",\n    ")
    with open(pyproject_toml_path, "w") as f:
        toml.dump(pyproject_toml, f, encoder=encoder)

    print(toml.dumps(pyproject_toml, encoder=encoder))


def format_dependency(forked_packages, name, versions):
    version = versions[name]
    if name not in forked_packages:
        formatted = f"{name}=={version}"
    else:
        formatted = f"{name}@https://github.com/oarepo/{name}/archive/oarepo-{version}.tar.gz"
    return formatted, name


if __name__ == "__main__":
    app()

