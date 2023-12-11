from pathlib import Path

import click
import subprocess
import toml
from requirements.parser import parse as parse_requirements


@click.command()
@click.argument("pdm_binary")
@click.argument("pdm_pyproject_toml_file")
@click.argument("output_pyproject_toml_file")
@click.option("--skip", help="Groups to skip", multiple=True)
@click.option(
    "--only", help="Groups to include (will exclude everything else)", multiple=True
)
@click.option(
    "--blacklisted-requirements-file", help="File with blacklisted requirements"
)
def export_requirements(
    pdm_binary,
    pdm_pyproject_toml_file,
    output_pyproject_toml_file,
    skip,
    only,
    blacklisted_requirements_file,
):
    with open(pdm_pyproject_toml_file, "r") as f:
        pdm_pyproject_toml = toml.load(f)

    with open(output_pyproject_toml_file, "r") as f:
        output_pyproject_toml = toml.load(f)

    blacklisted_requirements = set({})
    if blacklisted_requirements_file:
        with open(blacklisted_requirements_file, "r") as f:
            blacklisted_requirements.update(
                [x.name for x in parse_requirements(f.read())]
            )

    pdm_binary = Path(pdm_binary).resolve()

    pdm_directory = Path(pdm_pyproject_toml_file).parent

    # default
    requirements = pdm_export_requirements(pdm_binary, pdm_directory, "--prod")
    if "default" not in skip and ("default" in only or not only):
        output_pyproject_toml["project"]["dependencies"] = [
            r.line for r in requirements if r.name not in blacklisted_requirements
        ]
    default_requirements = {r.name for r in requirements}

    # optional groups
    for grp in pdm_pyproject_toml["project"]["optional-dependencies"].keys():
        if grp in skip:
            continue
        if only and grp not in only:
            continue

        if grp == "tests":
            arguments = ["--dev", "-G", "tests"]
        else:
            arguments = ["-G", grp]

        requirements = pdm_export_requirements(pdm_binary, pdm_directory, *arguments)

        output_pyproject_toml["project"]["optional-dependencies"][grp] = [
            r.line
            for r in requirements
            if r.name not in default_requirements
            and r.name not in blacklisted_requirements
        ]

    with open(output_pyproject_toml_file, "w") as f:
        toml.dump(f, output_pyproject_toml)


def pdm_export_requirements(pdm_binary, pdm_directory, *arguments):
    click.secho(
        f"Exporting requirements with {pdm_binary} {arguments} in {pdm_directory}",
        fg="yellow",
    )
    requirements = list(
        parse_requirements(
            subprocess.check_output(
                [
                    pdm_binary,
                    "export",
                    *arguments,
                    "--format",
                    "requirements",
                    "--without-hashes",
                ],
                cwd=pdm_directory,
            ).decode("utf-8")
        )
    )
    return requirements


if __name__ == "__main__":
    export_requirements()
