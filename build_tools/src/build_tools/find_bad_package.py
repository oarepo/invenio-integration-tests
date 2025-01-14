import shutil
import subprocess
import sys
from pathlib import Path


def load_freeze_from_file(path: Path) -> dict[str, str]:
    parts = [x.strip() for x in path.read_text().split("\n")]
    parts = [x for x in parts if x and "==" in x]
    return {
        part.split("==", maxsplit=1)[0].lower(): part.split("==", maxsplit=1)[1]
        for part in parts
    }


def dump_freeze(path: Path, freeze: dict[str, str]) -> None:
    path.write_text("\n".join(f"{k}=={v}" for k, v in freeze.items()))


def load_freeze_from_venv() -> dict[str, str]:
    output = subprocess.check_output(["uv", "pip", "freeze"], text=True)
    return {
        part.split("==", maxsplit=1)[0].lower(): part.split("==", maxsplit=1)[1]
        for part in output.split("\n")
        if part and "==" in part
    }


def install_from_freeze_file(freeze_file: Path, output_file: Path) -> None:
    with open(output_file, "w") as f:
        retcode = subprocess.call(
            ["uv", "pip", "install", "-r", str(freeze_file)], stdout=f, stderr=f
        )
        if retcode:
            raise Exception("Failed to install from freeze file")


def run_step(
    progress_dir: Path,
    dep: str,
    idx: int,
    working_deps: dict[str, str],
    failing_deps: dict[str, str],
    common_deps: list[str],
    nonworking_common_deps: dict[str, str],
    commands: list[str],
) -> bool:
    # dump actual freeze
    actual_freeze = load_freeze_from_venv()
    before_step_freeze_file = progress_dir / "01-freeze_before_step.txt"
    dump_freeze(before_step_freeze_file, actual_freeze)

    # install the package
    with open(progress_dir / "02-pip_install_output", "w") as f:
        retcode = subprocess.call(
            ["uv", "pip", "install", f"{dep}=={failing_deps[dep]}"], stdout=f, stderr=f
        )

    # if can not install, reinstall from the freeze file
    if retcode != 0:
        install_from_freeze_file(
            before_step_freeze_file,
            progress_dir / "03-reinstall_previous_state_pip_failed",
        )
        with open(progress_dir / "04-status-failed-pip", "w") as f:
            f.write("pip install failed")
        return False

    # store the current freeze
    actual_freeze = load_freeze_from_venv()
    after_install_freeze_file = progress_dir / "03-after_pip_install.txt"
    dump_freeze(after_install_freeze_file, actual_freeze)

    # run the commands
    with open(progress_dir / "04-test_command_output", "w") as f:
        retcode = subprocess.call(commands, stdout=f, stderr=f)
        if retcode != 0:
            # if failed, reinstall from the before step freeze file

            with open(progress_dir / "05-status-failed-commands", "w") as f:
                f.write("commands failed")

            install_from_freeze_file(
                before_step_freeze_file,
                progress_dir / "06-reinstall_previous_state_commands_failed",
            )
            return False
        with open(progress_dir / "05-status-ok", "w") as f:
            f.write("commands ok")

    return True


def find_bad_package(
    working_deps_file: Path,
    failing_deps_file: Path,
    progress_dir: Path,
    commands: list[str],
) -> int:
    progress_dir.mkdir(parents=True, exist_ok=True)

    working_deps = load_freeze_from_file(working_deps_file)
    failing_deps = load_freeze_from_file(failing_deps_file)

    deps_to_try = [
        k
        for k in working_deps.keys()
        if k in failing_deps and working_deps[k] != failing_deps[k]
    ]
    # deps_to_try.sort()
    nonworking_common_deps: dict[str, str] = {}

    if Path(".venv").exists():
        shutil.rmtree(".venv")

    subprocess.check_call(["uv", "venv", "--python", "python3.12", "--seed"])
    install_from_freeze_file(working_deps_file, progress_dir / "initial_install")

    idx = 0
    deps_count = len(deps_to_try)
    while deps_to_try:
        idx += 1
        dep = deps_to_try.pop(0)
        print(f"Checking {idx} / {deps_count} - {dep}")
        step_progress_dir = (
            progress_dir / f"{idx:06}__{dep}__{working_deps[dep]}__{failing_deps[dep]}"
        )
        step_progress_dir.mkdir(parents=True, exist_ok=True)
        (step_progress_dir / "next_common_deps.txt").write_text("\n".join(deps_to_try))
        step_ok = run_step(
            step_progress_dir,
            dep,
            idx,
            working_deps,
            failing_deps,
            deps_to_try,
            nonworking_common_deps,
            commands,
        )
        if step_ok:
            print(f"{dep} ok")
            step_progress_dir.rename(
                step_progress_dir.with_name(
                    f"{idx:06}__{dep}__{working_deps[dep]}__{failing_deps[dep]}__passed"
                )
            )
        else:
            print(f"{dep} failed")
            step_progress_dir.rename(
                step_progress_dir.with_name(
                    f"{idx:06}__{dep}__{working_deps[dep]}__{failing_deps[dep]}__failed"
                )
            )
            nonworking_common_deps[dep] = failing_deps[dep]
            dump_freeze(
                progress_dir / "nonworking_common_deps.txt", nonworking_common_deps
            )
    final_dependencies = load_freeze_from_venv()
    dump_freeze(progress_dir / "final_dependencies.txt", final_dependencies)

    return 0


if __name__ == "__main__":
    sys.exit(
        find_bad_package(
            Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4:]
        )
    )
