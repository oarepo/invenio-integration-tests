"""Create v tags for ordinary version tags.

This is a temporary command. It takes a github organization and optionally a list of repositories.
For each repository, it will read all its tags. If the tag looks like a version (e.g. `1.0.0`),
it will create a corresponding `v1.0.0` tag if it does not exist yet.

We will also modify build scripts in oarepo@rdm-14 to also create a 'v' tag for each release.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from packaging import version as packaging_version
from rich.console import Console

app = typer.Typer(help="Create missing v-prefixed git tags for GitHub repositories.")
console = Console()


def run_command(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process."""
    printable = " ".join(command)
    console.print(f"[dim]$ {printable}[/dim]")
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture_output,
        cwd=cwd,
    )


def is_version_tag(tag: str) -> bool:
    """Return True if the tag is a version without the v prefix."""
    if tag.startswith("v"):
        return False
    try:
        packaging_version.Version(tag)
        return True
    except packaging_version.InvalidVersion:
        return False


def get_repositories(organization: str) -> list[str]:
    """List repositories for the given GitHub organization using gh."""
    result = run_command(
        [
            "gh",
            "repo",
            "list",
            organization,
            "--limit",
            "1000",
            "--json",
            "name",
            "--jq",
            ".[].name",
        ]
    )
    repositories = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return repositories


def matches_any_pattern(name: str, patterns: list[str] | None) -> bool:
    if not patterns:
        return False
    return any(re.match(pattern, name) for pattern in patterns)


def filter_repositories(
    repositories: list[str],
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[str]:
    filtered: list[str] = []

    for repository in repositories:
        if include and not matches_any_pattern(repository, include):
            continue
        if exclude and matches_any_pattern(repository, exclude):
            continue
        filtered.append(repository)

    return filtered


def get_remote_tags(repository: str) -> dict[str, str]:
    """Return mapping of tag name -> commit sha for the given repository."""
    repo_url = f"https://github.com/{repository}.git"
    result = run_command(["git", "ls-remote", "--tags", repo_url])

    tags: dict[str, str] = {}
    peeled_tags: dict[str, str] = {}

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        sha, ref = line.split("\t", maxsplit=1)
        if not ref.startswith("refs/tags/"):
            continue

        tag_name = ref.removeprefix("refs/tags/")
        if tag_name.endswith("^{}"):
            peeled_tags[tag_name[:-3]] = sha
        else:
            tags[tag_name] = sha

    for tag_name, sha in peeled_tags.items():
        tags[tag_name] = sha

    return tags


def create_v_tag(
    repository: str, source_tag: str, sha: str, dry_run: bool = False
) -> None:
    """Create and push a v-prefixed tag from an isolated temporary bare repository."""
    target_tag = f"v{source_tag}"
    repo_url = f"https://github.com/{repository}.git"

    if dry_run:
        console.print(
            f"[yellow][DRY RUN][/yellow] Would create tag [bold]{target_tag}[/bold] in "
            f"[cyan]{repository}[/cyan] pointing to [magenta]{sha}[/magenta] "
            f"(from [bold]{source_tag}[/bold])"
        )
        return

    console.print(
        f"Creating tag [bold]{target_tag}[/bold] in [cyan]{repository}[/cyan] "
        f"pointing to [magenta]{sha}[/magenta] (from [bold]{source_tag}[/bold])"
    )

    with tempfile.TemporaryDirectory(prefix="create-v-tags-") as tmpdir:
        bare_repo = Path(tmpdir) / "repo.git"

        run_command(
            [
                "git",
                "init",
                "--bare",
                str(bare_repo),
            ],
            capture_output=True,
        )
        run_command(
            [
                "git",
                "--git-dir",
                str(bare_repo),
                "fetch",
                "--no-tags",
                repo_url,
                f"refs/tags/{source_tag}:refs/tags/{source_tag}",
            ],
            capture_output=True,
        )
        run_command(
            [
                "git",
                "--git-dir",
                str(bare_repo),
                "tag",
                target_tag,
                source_tag,
            ],
            capture_output=True,
        )
        run_command(
            [
                "git",
                "--git-dir",
                str(bare_repo),
                "push",
                repo_url,
                f"refs/tags/{target_tag}:refs/tags/{target_tag}",
            ],
            capture_output=True,
        )


@app.command()
def create_v_tags(
    organization: Annotated[str, typer.Argument(help="GitHub organization name")],
    repositories: Annotated[
        list[str] | None,
        typer.Argument(help="Optional repository names inside the organization"),
    ] = None,
    include: Annotated[
        list[str] | None,
        typer.Option(
            "--include",
            help="Only process repositories whose names match at least one regular expression",
        ),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            help="Skip repositories whose names match at least one regular expression",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be done without pushing any tags",
        ),
    ] = False,
) -> None:
    """Create missing v-prefixed tags for repositories in a GitHub organization."""
    if repositories:
        repository_names = repositories
    else:
        repository_names = get_repositories(organization)

    repository_names = filter_repositories(
        repository_names,
        include=include,
        exclude=exclude,
    )

    if not repository_names:
        console.print("[yellow]No repositories found.[/yellow]")
        return

    total_created = 0
    total_skipped = 0

    for repository_name in repository_names:
        full_repository = f"{organization}/{repository_name}"
        console.print()
        console.print(f"[bold cyan]=== {full_repository} ===[/bold cyan]")

        try:
            tags = get_remote_tags(full_repository)
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]Failed to list tags for {full_repository}[/red]")
            if exc.stdout:
                console.print(exc.stdout.strip())
            if exc.stderr:
                console.print(f"[red]{exc.stderr.strip()}[/red]")
            total_skipped += 1
            continue

        created_for_repo = 0

        for tag_name in sorted(tags):
            if not is_version_tag(tag_name):
                continue

            v_tag = f"v{tag_name}"
            if v_tag in tags:
                console.print(
                    f"Skipping [bold]{tag_name}[/bold]: [bold]{v_tag}[/bold] already exists"
                )
                continue

            try:
                create_v_tag(full_repository, tag_name, tags[tag_name], dry_run=dry_run)
                created_for_repo += 1
                total_created += 1
            except subprocess.CalledProcessError as exc:
                console.print(
                    f"[red]Failed to create {v_tag} in {full_repository}[/red]"
                )
                if exc.stdout:
                    console.print(exc.stdout.strip())
                if exc.stderr:
                    console.print(f"[red]{exc.stderr.strip()}[/red]")
                total_skipped += 1

        if created_for_repo == 0:
            console.print("[green]No missing v-tags found.[/green]")

    console.print(
        f"\n[bold green]Done.[/bold green] Created [bold]{total_created}[/bold] tag(s)"
        f"{' [yellow](dry run)[/yellow]' if dry_run else ''}. "
        f"Skipped/failed: [bold]{total_skipped}[/bold]."
    )


if __name__ == "__main__":
    app()
