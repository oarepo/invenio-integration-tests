import json
import subprocess
from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def find_built_packages(forks_json_path: Path, cesnet_pypi_url: str):
    """
    Check the selected forked packages and try to find the cesnet
    version on cesnet gitlab pypi sever.

    The input is a json file with the selected forks, as produced by
    select_forks_from_zenodo_freeze.py. The output is a json file with
    the same structure, but with an additional field "already_built"
    added to each package whose cesnet_version was found on the cesnet
    pypi server.
    """

    # load the forks json file
    json_data = json.loads(forks_json_path.read_text())

    for pkg in json_data.get("packages", []):
        pkg_name = pkg["name"]
        pkg_version = pkg["cesnet_version"]
        # query the cesnet pypi server for the package. Can not use json endpoint
        # as gitlab pypi server does not support it. Instead will use pip index versions
        # call.
        try:
            versions = json.loads(
                subprocess.check_output(
                    [
                        "pip",
                        "index",
                        "versions",
                        "--index-url",
                        cesnet_pypi_url + "/simple",
                        pkg_name,
                        "--json",
                    ],
                    text=True,
                )
            )
        except subprocess.CalledProcessError:
            versions = {"name": pkg_name, "versions": []}

        if pkg_version in versions.get("versions", []):
            pkg["already_built"] = True
            print(f"Package {pkg_name} version {pkg_version} already built.")
        else:
            pkg["already_built"] = False
            print(f"Package {pkg_name} version {pkg_version} NOT built.")

    # save the updated json file
    forks_json_path.write_text(json.dumps(json_data, indent=2))


if __name__ == "__main__":
    app()
