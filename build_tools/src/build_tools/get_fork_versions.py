import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def main(
    fork_definition: Annotated[
        Path, typer.Argument(help="Path to the fork definition json file")
    ],
    output_file: Annotated[Path, typer.Option(help="Path to the output file")] = None,
):
    forks = json.loads(fork_definition.read_text())

    if output_file:
        output_file.write_text(json.dumps([json.dumps(x) for x in forks["packages"]]))
    else:
        print(json.dumps([json.dumps(x) for x in forks["packages"]]))


if __name__ == "__main__":
    app()
