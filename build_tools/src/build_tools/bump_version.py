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
def main(pyproject_toml_path: Annotated[Path, typer.Argument(help="Path to the output file")],
        version_py_path: Annotated[Path, typer.Argument(help="Path to the version.py file")]):

    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

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


if __name__ == "__main__":
    app()

