import json
from pathlib import Path

import click


@click.group()
def cli():
    """Invenio Integration Tests CLI."""
    pass


@cli.command("setup")
@click.argument(
    "input_config", type=click.Path(path_type=Path, resolve_path=True, exists=True)
)
@click.argument(
    "preprocessed_config", type=click.Path(path_type=Path, resolve_path=True)
)
def setup(input_config: Path, preprocessed_config: Path):
    """Preprocess the input configuration and save it to the preprocessed configuration path."""
    import yaml

    with input_config.open() as f:
        config = yaml.safe_load(f)

    packages = config.pop("packages", [])
    supported_invenio_version = config.pop("invenio-version", None)
    patches = []
    entrypoints = {}
    for package_def in packages:
        package_name = package_def.pop("name")
        _unused_depends = package_def.pop("depends", [])
        _unused_dependencies = package_def.pop("dependencies", [])
        _unused_tests = package_def.pop("tests", [])
        if not package_name:
            raise ValueError(
                f"Package definition must include a 'name' field, got {package_def}"
            )
        for feature in package_def.pop("features", []):
            if isinstance(feature, str):
                patches.append(feature)
                continue
            feature_name = feature.pop("name")
            feature_base = feature.pop("base")
            feature_str = f"oarepo/{package_name}@{feature_name}[{feature_base}]"

            invenio_version = feature.pop("invenio-version", None)
            if invenio_version:
                feature_str += invenio_version

            patches.append(feature_str)
            assert not feature, f"Unexpected keys in feature definition: {feature}"

        package_entrypoints = package_def.pop("entrypoints", {})
        if package_entrypoints:
            entrypoints[package_name] = package_entrypoints

        assert not package_def, f"Unexpected keys in package definition: {package_def}"

    assert not config, f"Unexpected keys in configuration: {config}"

    with preprocessed_config.open("w") as f:
        json.dump(
            {
                "invenio-version": supported_invenio_version,
                "patches": patches,
                "entrypoints": entrypoints,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    cli()
