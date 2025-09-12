import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def main(
    pypi_versions_file: Annotated[
        Path, typer.Argument(help="Path to the cesnet_pypi_versions.json file")
    ],
    cesnet_pypi_versions_file: Annotated[
        Path, typer.Argument(help="Path to the cesnet_pypi_versions.json file")
    ],
    not_uploaded_packages_file: Annotated[
        Path, typer.Argument(help="Path to the file with not uploaded packages")
    ],
    output_file: Annotated[
        Path, typer.Argument(help="Path to the output file for non-existing packages")
    ],
):

    # files look like [{"name": "package", "versions": ["x.y.z"]}, ...]
    pypi_versions = json.loads(pypi_versions_file.read_text())
    cesnet_pypi_versions = json.loads(cesnet_pypi_versions_file.read_text())
    not_uploaded_packages = set(
        x.strip()
        for x in not_uploaded_packages_file.read_text().splitlines()
        if x.strip()
    )

    non_existing = []

    for pkg in pypi_versions:
        name = pkg["name"]
        versions = pkg["versions"]

        cesnet_pkg = next((p for p in cesnet_pypi_versions if p["name"] == name), None)
        if not cesnet_pkg:
            for version in reversed(versions):
                if f"{name}=={version}" in not_uploaded_packages:
                    continue
                non_existing.append(f"{name}=={version}")
            continue

        cesnet_versions = cesnet_pkg["versions"]
        for version in reversed(versions):
            if version not in cesnet_versions:
                if f"{name}=={version}" in not_uploaded_packages:
                    continue
                non_existing.append(f"{name}=={version}")

    output_file.write_text("\n".join(non_existing) + "\n")


if __name__ == "__main__":
    app()
