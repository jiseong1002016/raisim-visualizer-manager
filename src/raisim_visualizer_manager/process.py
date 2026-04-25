from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TextIO


def ensure_parent(path: str | None) -> None:
    if path:
        parent = Path(path).expanduser().parent
        if str(parent):
            parent.mkdir(parents=True, exist_ok=True)


def terminate_process(proc: subprocess.Popen | None, timeout: float = 5.0) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)


def run_command(
    command: list[str],
    *,
    cwd: str | None,
    env: dict[str, str],
    timeout: float | None,
    log: TextIO | None,
) -> int:
    stdout = log if log is not None else None
    proc = subprocess.Popen(command, cwd=cwd or None, env=env, stdout=stdout, stderr=subprocess.STDOUT)
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        terminate_process(proc)
        return 124
