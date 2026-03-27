"""Create normalized v-tags for version tags.

This is a temporary command. It takes a GitHub organization and optionally a list
of repositories. For each repository, it reads all tags. If a tag looks like a
version (e.g. ``1.0.0`` or ``1.0.0.dev3``), it creates a corresponding
normalized ``v`` tag if it does not exist yet.

Normalization rules:
- ``1.0.0`` -> ``v1.0.0``
- ``1.0.0.dev3`` -> ``v1.0.0dev3``

If the repository already contains a dotted v-tag such as ``v1.0.0.dev3``, it is
renamed to the normalized dotless form ``v1.0.0dev3``.
"""

from __future__ import annotations

import contextlib
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from packaging import version as packaging_version
from rich.console import Console

app = typer.Typer(help="Create normalized v-prefixed git tags for GitHub repositories.")
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


def parse_version_tag(tag: str) -> packaging_version.Version | None:
    """Parse a version tag without the leading v."""
    if tag.startswith("v"):
        return None
    try:
        return packaging_version.Version(tag)
    except packaging_version.InvalidVersion:
        return None


def parse_v_version_tag(tag: str) -> packaging_version.Version | None:
    """Parse a version tag with the leading v."""
    if not tag.startswith("v"):
        return None
    try:
        return packaging_version.Version(tag[1:])
    except packaging_version.InvalidVersion:
        return None


def normalize_version_string(version: packaging_version.Version) -> str:
    """Return a normalized version string with dotless dev/prerelease segments."""
    normalized = str(version)
    normalized = normalized.replace(".dev", "dev")
    normalized = normalized.replace(".post", "post")
    return normalized


def normalize_v_tag_name(tag: str) -> str | None:
    """Normalize a v-prefixed tag name."""
    version = parse_v_version_tag(tag)
    if version is None:
        return None

    normalized_without_v = normalize_version_string(version)
    normalized_with_v = f"v{normalized_without_v}"

    if tag == normalized_with_v:
        return tag

    if "." in tag[1:]:
        return normalized_with_v

    return None


def get_repositories(organization: str) -> list[str]:
    """List non-archived repositories for the given GitHub organization using gh."""
    result = run_command(
        [
            "gh",
            "repo",
            "list",
            organization,
            "--limit",
            "1000",
            "--json",
            "name,isArchived",
            "--jq",
            ".[] | select(.isArchived | not) | .name",
        ]
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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


@contextlib.contextmanager
def create_bare_repo(repo_url: str):
    """Create a temporary bare repository with origin configured."""
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
                "remote",
                "add",
                "origin",
                repo_url,
            ],
            capture_output=True,
        )
        yield bare_repo


def ensure_tag_in_bare_repo(bare_repo: Path, source_tag: str) -> None:
    """Fetch a tag into the temporary bare repo."""
    run_command(
        [
            "git",
            "--git-dir",
            str(bare_repo),
            "fetch",
            "--no-tags",
            "origin",
            f"refs/tags/{source_tag}:refs/tags/{source_tag}",
        ],
        capture_output=True,
    )


def create_local_tag(bare_repo: Path, target_tag: str, source_tag: str) -> None:
    """Create or replace a tag in the temporary bare repo."""
    run_command(
        [
            "git",
            "--git-dir",
            str(bare_repo),
            "tag",
            "-f",
            target_tag,
            source_tag,
        ],
        capture_output=True,
    )


def push_tag(bare_repo: Path, repo_url: str, tag_name: str) -> None:
    """Push a single tag to origin."""
    run_command(
        [
            "git",
            "--git-dir",
            str(bare_repo),
            "push",
            repo_url,
            f"refs/tags/{tag_name}:refs/tags/{tag_name}",
        ],
        capture_output=True,
    )


def delete_remote_tag(bare_repo: Path, repo_url: str, tag_name: str) -> None:
    """Delete a single remote tag."""
    run_command(
        [
            "git",
            "--git-dir",
            str(bare_repo),
            "push",
            repo_url,
            f":refs/tags/{tag_name}",
        ],
        capture_output=True,
    )


def create_v_tag(
    repository: str,
    source_tag: str,
    target_tag: str,
    sha: str,
    dry_run: bool = False,
) -> None:
    """Create and push a normalized v-prefixed tag from an isolated temporary bare repository."""
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

    with create_bare_repo(repo_url) as bare_repo:
        ensure_tag_in_bare_repo(bare_repo, source_tag)
        create_local_tag(bare_repo, target_tag, source_tag)
        push_tag(bare_repo, repo_url, target_tag)


def rename_v_tag(
    repository: str,
    old_tag: str,
    new_tag: str,
    sha: str,
    dry_run: bool = False,
) -> None:
    """Rename a dotted v-tag to its normalized dotless form."""
    repo_url = f"https://github.com/{repository}.git"

    if dry_run:
        console.print(
            f"[yellow][DRY RUN][/yellow] Would rename tag [bold]{old_tag}[/bold] to "
            f"[bold]{new_tag}[/bold] in [cyan]{repository}[/cyan] "
            f"pointing to [magenta]{sha}[/magenta]"
        )
        return

    console.print(
        f"Renaming tag [bold]{old_tag}[/bold] to [bold]{new_tag}[/bold] in "
        f"[cyan]{repository}[/cyan] pointing to [magenta]{sha}[/magenta]"
    )

    with create_bare_repo(repo_url) as bare_repo:
        ensure_tag_in_bare_repo(bare_repo, old_tag)
        create_local_tag(bare_repo, new_tag, old_tag)
        push_tag(bare_repo, repo_url, new_tag)
        delete_remote_tag(bare_repo, repo_url, old_tag)


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
    """Create normalized v-prefixed tags for repositories in a GitHub organization."""
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
    total_renamed = 0
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

        changed_for_repo = 0

        # First rename dotted v-tags to normalized dotless v-tags.
        for tag_name in sorted(tags):
            normalized_v_tag = normalize_v_tag_name(tag_name)
            if normalized_v_tag is None or normalized_v_tag == tag_name:
                continue

            if normalized_v_tag in tags:
                console.print(
                    f"Skipping rename of [bold]{tag_name}[/bold]: "
                    f"[bold]{normalized_v_tag}[/bold] already exists"
                )
                continue

            try:
                rename_v_tag(
                    full_repository,
                    tag_name,
                    normalized_v_tag,
                    tags[tag_name],
                    dry_run=dry_run,
                )
                changed_for_repo += 1
                total_renamed += 1
                tags[normalized_v_tag] = tags[tag_name]
            except subprocess.CalledProcessError as exc:
                console.print(
                    f"[red]Failed to rename {tag_name} to {normalized_v_tag} "
                    f"in {full_repository}[/red]"
                )
                if exc.stdout:
                    console.print(exc.stdout.strip())
                if exc.stderr:
                    console.print(f"[red]{exc.stderr.strip()}[/red]")
                total_skipped += 1

        # Then create missing normalized v-tags from non-v source tags.
        for tag_name in sorted(tags):
            version = parse_version_tag(tag_name)
            if version is None:
                continue

            normalized_target_tag = f"v{normalize_version_string(version)}"
            if normalized_target_tag in tags:
                console.print(
                    f"Skipping [bold]{tag_name}[/bold]: "
                    f"[bold]{normalized_target_tag}[/bold] already exists"
                )
                continue

            try:
                create_v_tag(
                    full_repository,
                    tag_name,
                    normalized_target_tag,
                    tags[tag_name],
                    dry_run=dry_run,
                )
                changed_for_repo += 1
                total_created += 1
                tags[normalized_target_tag] = tags[tag_name]
            except subprocess.CalledProcessError as exc:
                console.print(
                    f"[red]Failed to create {normalized_target_tag} in "
                    f"{full_repository}[/red]"
                )
                if exc.stdout:
                    console.print(exc.stdout.strip())
                if exc.stderr:
                    console.print(f"[red]{exc.stderr.strip()}[/red]")
                total_skipped += 1

        if changed_for_repo == 0:
            console.print("[green]No missing or malformed v-tags found.[/green]")

    console.print(
        f"\n[bold green]Done.[/bold green] Created [bold]{total_created}[/bold] tag(s), "
        f"renamed [bold]{total_renamed}[/bold] tag(s)"
        f"{' [yellow](dry run)[/yellow]' if dry_run else ''}. "
        f"Skipped/failed: [bold]{total_skipped}[/bold]."
    )


if __name__ == "__main__":
    app()
