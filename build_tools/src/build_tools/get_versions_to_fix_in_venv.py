import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from build_tools.utils.pip import parse_pip_freeze

app = typer.Typer()


@app.command()
def main(
    rdmversions_json_file: Annotated[
        Path, typer.Argument(help="Path to the rdm_versions.json file")
    ],
    invenio_forks_json_file: Annotated[
        Path, typer.Argument(help="Path to the invenio-forks.json file")
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the output text file to write the versions to fix"
        ),
    ],
):
    rdm_versions = json.loads(rdmversions_json_file.read_text())
    invenio_forks = json.loads(invenio_forks_json_file.read_text())

    rdm_versions_dict = {pkg["name"].lower(): pkg["version"] for pkg in rdm_versions}

    freeze = subprocess.check_output(
        ["uv", "pip", "freeze", "--python", ".venv/bin/python"], text=True
    )
    installed_packages = list(parse_pip_freeze(freeze))
    out = []
    for pkg in installed_packages:
        if pkg.name in rdm_versions_dict and pkg.name not in invenio_forks["pkg_index"]:
            out.append(f"{pkg.name}=={rdm_versions_dict[pkg.name]}")
    output_file.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    app()
