import json
from pathlib import Path
from typing import Annotated, NamedTuple

import typer
from configupdater import ConfigUpdater, Option

app = typer.Typer()

"""
The fork_config_file looks like:
{
    "entrypoints": [{
        "test": "long string of separated group\n    name=value"
    }, {...}]
}
"""

EntryPoint = NamedTuple(
    "EntryPoint", [("group", str), ("name", str), ("value", str | None)]
)


@app.command()
def main(
    fork_config_file: Annotated[
        Path, typer.Argument(help="Path to the json file with package config")
    ],
    setup_cfg_file: Annotated[Path, typer.Argument(help="Path to the setup.cfg file")],
):
    fork_config = json.loads(fork_config_file.read_text())

    cfg = ConfigUpdater()
    cfg.read_string(setup_cfg_file.read_text())

    current_group: str | None = None

    for ep in fork_config.get("entrypoints", []):
        if "tests" not in ep:
            continue
        eps = ep["tests"].strip().split("\n")
        for e in eps:
            if not e.strip():
                continue
            if not e.startswith(" "):
                current_group = e.strip().strip("=").strip()
                continue
            e = e.strip()
            key, value = e.split("=", 1)
            key = key.strip()
            value = value.strip()
            print("Adding entry point", current_group, key, value)
            add_entry_point(cfg, EntryPoint(current_group, key, value))

    if current_group:
        print(cfg)
        cfg.write(setup_cfg_file.open("w"))


def write_values(opt: Option, values: list[str], format=True):
    if format:
        values = [val.replace(" ", "") for val in values]
        values = [val.replace("=", " = ") for val in values]
    opt.set_values(values)


def load_ep_values(ep_string: Option):
    return [x.strip().replace(" ", "") for x in ep_string.as_list() if x.strip()]


def add_entry_point(cfg: ConfigUpdater, entry: EntryPoint):
    eps = cfg["options.entry_points"]
    if entry.group not in eps:
        eps[entry.group] = ""
    values = load_ep_values(eps[entry.group])
    if f"{entry.name}={entry.value}" in values:
        return
    values.append(f"{entry.name}={entry.value}")
    write_values(eps[entry.group], values)


if __name__ == "__main__":
    app()
