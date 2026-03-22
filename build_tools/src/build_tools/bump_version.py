from pathlib import Path
from typing import Annotated

import semver
import toml
import typer

app = typer.Typer()


@app.command()
def main(
    pyproject_toml_path: Annotated[
        Path, typer.Argument(help="Path to the output file")
    ],
    version_py_path: Annotated[
        Path, typer.Argument(help="Path to the version.py file")
    ],
):

    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

    # increment the version
    version = semver.Version.parse(pyproject_toml["project"]["version"])
    version = version.bump_patch()
    # read the invenio-app-rdm version and add any alpha/beta/dev/rc suffix
    dependencies = pyproject_toml["project"]["dependencies"]
    for dep in dependencies:
        if dep.startswith("invenio-app-rdm"):
            invenio_app_rdm_version = dep.split("==")[1]
            # "invenio-app-rdm==14.0.0b5.dev4+oarepo.2.3wqazamelrcgbkdl",
            app_rdm_version = semver.Version.parse(invenio_app_rdm_version[:-1])
            version = version.replace(prerelease=app_rdm_version.prerelease)
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
