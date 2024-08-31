import functools
import json
from pathlib import Path
from pprint import pprint
from typing import Annotated
import yaml
from semver import Version

import typer

app = typer.Typer()

@app.command()
def main(oarepo_version: str,
        requirements_json_file: Annotated[Path, typer.Argument(help="Path to the requirements.json file")],
        fork_definition: Annotated[Path, typer.Argument(help="Path to the fork definition file")]):

    reqs = json.loads(requirements_json_file.read_text())
    forks = yaml.safe_load(fork_definition.read_text())

    reqs = {
        x['name']: x['version'] for x in reqs
    }

    for pkg in forks['packages']:
        try:
            version = get_package_version(pkg, oarepo_version, reqs)
            print(version)
        except:
            print("Error in fork definition")
            pprint(pkg)
            raise

def get_package_version(forked_package, oarepo_version, reqs):
    if oarepo_version != str(forked_package["oarepo"]):
        return None
    invenio_version = Version.parse(reqs[forked_package['name']])
    matching_features = []
    for feature in forked_package['features']:
        if not "invenio-version" in feature:
            matching_features.append(feature['name'])
        feature_invenio_version = feature['invenio-version']
        feature_invenio_version = [complete_version(x.strip()) for x in feature_invenio_version.split(",")]
        if all(invenio_version.match(x) for x in feature_invenio_version):
            matching_features.append(feature['name'])
    return {
        "package": forked_package['name'],
        "version": str(invenio_version),
        "features": matching_features
    }

def complete_version(incomplete_version):
    while len(incomplete_version.split(".")) < 3:
        incomplete_version += ".0"
    return incomplete_version

if __name__ == "__main__":
    app()
