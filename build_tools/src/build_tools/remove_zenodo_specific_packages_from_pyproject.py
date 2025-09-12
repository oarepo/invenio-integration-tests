from pathlib import Path
from typing import Annotated

import tomli
import tomli_w
import typer

app = typer.Typer()


@app.command()
def main(
    pyproject_toml_file: Annotated[
        Path, typer.Argument(help="Path to the pyproject.toml file")
    ],
):
    # Read the pyproject.toml file
    project = tomli.loads(pyproject_toml_file.read_text())
    dependencies = project.get("project", {}).get("dependencies", [])
    app_rdm_dependency = None
    for dep in list(dependencies):
        if dep.startswith("invenio-app-rdm"):
            app_rdm_dependency = dep
        if dep.startswith("invenio-swh"):
            print("Removing invenio-swh from pyproject.toml")
            dependencies.remove(dep)
        if not dep.startswith("invenio-"):
            print("Removing non-invenio dependency from pyproject.toml:", dep)
            dependencies.remove(dep)

    project["project"]["dependencies"] = dependencies

    # tests
    if app_rdm_dependency is None:
        raise ValueError("invenio-app-rdm dependency not found in pyproject.toml")
    # add [tests] extra dependencies to app_rdm_dependency
    if "[" in app_rdm_dependency:
        app_rdm_dependency = app_rdm_dependency.replace(
            "[", "[tests,"
        )  # add tests to existing extras
    else:
        app_rdm_dependency = app_rdm_dependency.replace(
            "invenio-app-rdm", "invenio-app-rdm[tests]"
        )  # add tests extras
    dev_group = project["dependency-groups"]["dev"]
    dev_group.append(app_rdm_dependency)
    project["dependency-groups"]["dev"] = dev_group
    project["dependency-groups"]["tests"] = dev_group

    pyproject_toml_file.write_text(tomli_w.dumps(project))


if __name__ == "__main__":
    app()
