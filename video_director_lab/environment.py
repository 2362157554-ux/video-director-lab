from __future__ import annotations

import importlib.util
import shutil
import subprocess
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ToolCheck:
    name: str
    command: str
    available: bool
    detail: str = ""


def check_command(name: str, executable: str, version_args: tuple[str, ...]) -> ToolCheck:
    command = " ".join((executable, *version_args))
    if shutil.which(executable) is None:
        return ToolCheck(name=name, command=command, available=False, detail="not found on PATH")

    try:
        result = subprocess.run(
            (executable, *version_args),
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except OSError as exc:
        return ToolCheck(name=name, command=command, available=False, detail=str(exc))
    except subprocess.TimeoutExpired:
        return ToolCheck(name=name, command=command, available=False, detail="timed out")

    detail = (result.stdout or result.stderr).strip().splitlines()
    return ToolCheck(
        name=name,
        command=command,
        available=result.returncode == 0,
        detail=detail[0] if detail else f"exit {result.returncode}",
    )


def check_python_module(module_name: str, label: str | None = None) -> ToolCheck:
    label = label or module_name
    available = importlib.util.find_spec(module_name) is not None
    return ToolCheck(
        name=label,
        command=f'python -c "import {module_name}"',
        available=available,
        detail="importable" if available else "module missing",
    )


def run_environment_checks(include_jianying: bool = True) -> tuple[ToolCheck, ...]:
    checks: list[ToolCheck] = [
        check_command("Node.js", "node", ("-v",)),
        check_command("npm", "npm", ("-v",)),
        check_command("Python", "python", ("--version",)),
        check_command("pip", "python", ("-m", "pip", "--version")),
        check_command("ffmpeg", "ffmpeg", ("-version",)),
    ]

    if include_jianying:
        checks.append(check_python_module("pyJianYingDraft", "pyJianYingDraft"))

    return tuple(checks)


def summarize_missing_tools(checks: Iterable[ToolCheck]) -> tuple[str, ...]:
    return tuple(check.name for check in checks if not check.available)
