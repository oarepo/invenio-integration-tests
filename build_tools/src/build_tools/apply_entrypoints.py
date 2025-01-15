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
        "remove": "*", (or a list of entrypoints to remove)
        "keep": [
            {
                "group": "invenio_assets.webpack",
                "name": "invenio_app_rdm_theme"
            }
        ],
        "add": [
            {
                group: "invenio_assets.webpack",
                name: "invenio_app_rdm_theme",
                value: "rdm_theme/webpack.config.js"
            }
        ]
    }, {...}]
}
"""

EntryPoint = NamedTuple(
    "EntryPoint", [("group", str), ("name", str), ("value", str | None)]
)


@app.command()
def main(
    fork_config_file: Annotated[
        Path, typer.Argument(help="Path to the rdm_requirements.json file")
    ],
    setup_cfg_file: Annotated[Path, typer.Argument(help="Path to the setup.cfg file")],
):
    fork_config = json.loads(fork_config_file.read_text())

    cfg = ConfigUpdater()
    cfg.read_string(setup_cfg_file.read_text())

    for entrypoint in fork_config.get("entrypoints", []):
        kept_entrypoints: set[EntryPoint] = set()
        for ep in entrypoint.get("keep", []):
            kept_entrypoints.add(EntryPoint(ep["group"], ep["name"], None))
        if "remove" in entrypoint:
            to_remove = entrypoint["remove"]
            if not isinstance(to_remove, list):
                to_remove = [to_remove]
            for ep in to_remove:
                if ep == "*":
                    remove_all_entrypoints(cfg, kept_entrypoints)
                else:
                    remove_entry_point(
                        cfg, EntryPoint(ep["group"], ep["name"], None), kept_entrypoints
                    )
        if "add" in entrypoint:
            to_add = entrypoint["add"]
            if not isinstance(to_add, list):
                to_add = [to_add]
            for ep in to_add:
                add_entry_point(
                    cfg,
                    EntryPoint(ep["group"], ep["name"], ep["value"]),
                )
    for dep in fork_config.get("dependencies", []):
        kept_dependencies: set[str] = set()
        extra = dep.get("extra", None)
        for d in dep.get("keep", []):
            kept_dependencies.add(d.strip())
        if "remove" in dep:
            to_remove = dep["remove"]
            if not isinstance(to_remove, list):
                to_remove = [to_remove]
            for d in to_remove:
                if d == "*":
                    remove_all_dependencies(cfg, extra, kept_dependencies)
                else:
                    remove_dependency(cfg, extra, d, kept_dependencies)
        if "add" in dep:
            to_add = dep["add"]
            if not isinstance(to_add, list):
                to_add = [to_add]
            for d in to_add:
                add_dependency(cfg, extra, d)

    print(cfg)
    cfg.write(setup_cfg_file.open("w"))


def write_values(opt: Option, values: list[str], format=True):
    if format:
        values = [val.replace(" ", "") for val in values]
        values = [val.replace("=", " = ") for val in values]
    opt.set_values(values)


def load_ep_values(ep_string: Option):
    return [x.strip().replace(" ", "") for x in ep_string.as_list() if x.strip()]


def remove_all_dependencies(
    cfg: ConfigUpdater, extra: str | None, kept_dependencies: set[str]
):
    if extra:
        deps = cfg["options.extras_require"][extra]
    else:
        deps = cfg["options.install_requires"]
    values = load_ep_values(deps)
    values = [val for val in values if val in kept_dependencies]
    if values:
        write_values(deps, values, format=False)
    else:
        if extra:
            del cfg["options.extras_require"][extra]
        else:
            del cfg["options.install_requires"]


def remove_dependency(
    cfg: ConfigUpdater, extra: str | None, dep: str, kept_dependencies: set[str]
):
    dep = dep.strip().replace(" ", "")
    if extra:
        deps = cfg["options.extras_require"][extra]
    else:
        deps = cfg["options.install_requires"]
    values = load_ep_values(deps)
    values = [val for val in values if val != dep]
    if values:
        write_values(deps, values, format=False)
    else:
        if extra:
            del cfg["options.extras_require"][extra]
        else:
            del cfg["options.install_requires"]


def add_dependency(cfg: ConfigUpdater, extra: str | None, dep: str):
    dep = dep.strip().replace(" ", "")
    if extra:
        if extra not in cfg["options.extras_require"]:
            cfg["options.extras_require"][extra] = ""
        deps = cfg["options.extras_require"][extra]
    else:
        deps = cfg["options.install_requires"]
    values = load_ep_values(deps)
    if dep not in values:
        values.append(dep)
    write_values(deps, values, format=False)


def remove_all_entrypoints(cfg: ConfigUpdater, kept_entrypoints: set[EntryPoint]):
    eps = cfg["options.entry_points"]
    for group, values in eps.items():
        values = load_ep_values(values)
        kept_in_group = [ep.name for ep in kept_entrypoints if ep.group == group]
        values = [
            val
            for val in values
            if any(val.startswith(kept + "=") for kept in kept_in_group)
        ]
        if values:
            write_values(eps[group], values)
        else:
            del eps[group]


def remove_entry_point(
    cfg: ConfigUpdater, entry: EntryPoint, kept_entrypoints: set[EntryPoint]
):
    if entry in kept_entrypoints:
        return

    eps = cfg["options.entry_points"]
    if entry.group not in eps:
        return
    values = load_ep_values(eps[entry.group])
    values = [
        val in values if not val.startswith(entry.name + "=") else val for val in values
    ]
    values = [val.replace("=", " = ") for val in values]
    if values:
        write_values(eps[entry.group], values)
    else:
        del eps[entry.group]


def add_entry_point(cfg: ConfigUpdater, entry: EntryPoint):
    eps = cfg["options.entry_points"]
    remove_entry_point(cfg, entry, set())
    if entry.group not in eps:
        eps[entry.group] = ""
    values = load_ep_values(eps[entry.group])
    values.append(f"{entry.name}={entry.value}")
    write_values(eps[entry.group], values)


if __name__ == "__main__":
    app()
