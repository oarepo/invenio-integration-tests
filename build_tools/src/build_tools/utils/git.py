import contextlib
import subprocess
import tempfile


@contextlib.contextmanager
def clone_repository(url: str, tag: str | None = None, upstream: str | None = None):

    with tempfile.TemporaryDirectory(suffix=url.split("/")[-1]) as tmpdir:
        print(f"Cloning {url}")
        subprocess.check_call(["git", "clone", url, tmpdir])
        if tag:
            print(f"Checking out {tag}")
            subprocess.check_call(["git", "checkout", tag], cwd=tmpdir)

        if upstream:
            print(f"Adding upstream {upstream}")
            subprocess.check_call(
                ["git", "remote", "add", "upstream", upstream], cwd=tmpdir
            )

        print("Fetching all")
        subprocess.check_call(["git", "fetch", "--all"], cwd=tmpdir)

        yield tmpdir


def get_nearest_version_tag(tmpdir: str) -> str:
    print(
        "Calling git describe --tags --abbrev=0 --match v[0-9]* to get nearest version"
    )
    nearest_version = subprocess.check_output(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*"],
        cwd=tmpdir,
        text=True,
    ).strip()
    print(f"Nearest version is {nearest_version}")
    return nearest_version


def get_commit(tmpdir: str) -> str:
    print("Calling git rev-parse HEAD to get current commit")
    commit = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=tmpdir,
        text=True,
    ).strip()
    print(f"Current commit: {commit}")
    return commit
