import re
from collections import namedtuple
from typing import Generator

ParsedVersion = namedtuple(
    "ParsedVersion", ["name", "version", "github_repo", "github_tag", "commit"]
)


def extract_version(version_str: str) -> tuple[int, ...]:
    ret = []

    for part in version_str.split("."):
        res = (re.split("[a-z]", part))[0]

        if not res:
            continue

        ret.append(int(res))

    return tuple(ret)


def check_pkg_version(actual_pkg_version: str | None, fork_version: str) -> bool:
    if actual_pkg_version is None:
        return False

    fork_version_inequalities = fork_version.split(",")
    actual_pkg_version_tuple = extract_version(actual_pkg_version)
    for ineq in fork_version_inequalities:
        op = ""
        while ineq[0] in ["<", ">", "="]:
            op += ineq[0]
            ineq = ineq[1:]
        tested_version_tuple = tuple(int(x) for x in ineq.split("."))
        if op == "<":
            if actual_pkg_version_tuple >= tested_version_tuple:
                return False
        elif op == ">":
            if actual_pkg_version_tuple <= tested_version_tuple:
                return False
        elif op == "==":
            if actual_pkg_version_tuple != tested_version_tuple:
                return False
        elif op == ">=":
            if actual_pkg_version_tuple < tested_version_tuple:
                return False
        elif op == "<=":
            if actual_pkg_version_tuple > tested_version_tuple:
                return False
        else:
            raise ValueError(f"Unknown operator {op}")
    return True


def parse_pip_freeze(output: str) -> Generator[ParsedVersion, None, None]:
    for part in output.split("\n"):
        part = part.strip()
        if part.startswith("#") or not part:
            continue
        if ";" in part:
            part = part.split(";", maxsplit=1)[0].strip()
        if "==" in part:
            name, version = part.split("==", maxsplit=1)
            name = name.strip().lower()
            version = version.strip()
            yield ParsedVersion(name, version, None, None, "")
        elif "@ git+" in part:
            # github dependence in the form of invenio-app-rdm @ git+https://github.com/inveniosoftware/invenio-app-rdm@eee215c4bc9b7b89ec4a7eb633d145aaab008a3b
            name, rest = part.split(" @ git+", maxsplit=1)
            if "@" in rest:
                url, tag = rest.split("@", maxsplit=1)
            else:
                url = rest
                tag = None
            if url.endswith(".git"):
                url = url[: -len(".git")]
            if url.startswith("git+"):
                url = url[5:]
            yield ParsedVersion(name.lower(), None, url, tag, "")
        elif part.startswith("-e "):
            # zenodo specific local packages, skip those
            continue
        else:
            raise ValueError(f"Cannot parse requirement line: {part}")
