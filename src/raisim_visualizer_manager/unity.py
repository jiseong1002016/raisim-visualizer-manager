from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .process import ensure_parent


def configure_gui_port(gui_settings: str, port: int, backup_dir: str | None = None) -> bool:
    path = Path(gui_settings).expanduser()
    if not path.is_file():
        return False
    if backup_dir:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, Path(backup_dir) / "gui_settings.before.xml")
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(r'<ip_port value="[0-9]+"\s*/>', f'<ip_port value="{int(port)}"/>', text)
    if count <= 0:
        return False
    path.write_text(new_text, encoding="utf-8")
    if backup_dir:
        shutil.copy2(path, Path(backup_dir) / "gui_settings.used.xml")
    return True


def launch_unity(binary: str, display: str, width: int, height: int, log_path: str) -> subprocess.Popen:
    if not Path(binary).expanduser().is_file():
        raise FileNotFoundError(f"Unity binary not found: {binary}")
    ensure_parent(log_path)
    env = dict(os.environ)
    env["DISPLAY"] = display
    log_f = open(log_path, "ab")
    proc = subprocess.Popen(
        [
            str(Path(binary).expanduser()),
            "-screen-fullscreen", "0",
            "-screen-width", str(int(width)),
            "-screen-height", str(int(height)),
            "-logFile", log_path,
        ],
        stdout=log_f,
        stderr=subprocess.STDOUT,
        env=env,
    )
    proc._raisim_visualizer_log_f = log_f
    return proc


def position_window(
    *,
    display: str,
    pid: int | None,
    title_regex: str,
    x: int,
    y: int,
    width: int,
    height: int,
    attempts: int = 30,
) -> tuple[str, str, dict[str, str]]:
    window = ""
    for _ in range(max(1, attempts)):
        if pid is not None:
            out = _run_quiet(["xdotool", "search", "--pid", str(int(pid))], display=display)
            window = out.splitlines()[0] if out else ""
        if not window:
            out = _run_quiet(["xdotool", "search", "--onlyvisible", "--name", title_regex], display=display)
            window = out.splitlines()[0] if out else ""
        if window:
            _run_quiet(["xdotool", "windowmove", window, str(int(x)), str(int(y))], display=display)
            _run_quiet(["xdotool", "windowsize", window, str(int(width)), str(int(height))], display=display)
            _run_quiet(["xdotool", "windowactivate", window], display=display)
            time.sleep(1.0)
            geom = _window_geometry(window, display)
            return window, f"+{geom.get('X', str(x))},{geom.get('Y', str(y))}", geom
        time.sleep(1.0)
    return "", f"+{int(x)},{int(y)}", {}


def _window_geometry(window: str, display: str) -> dict[str, str]:
    geom = _run_quiet(["xdotool", "getwindowgeometry", "--shell", window], display=display)
    values: dict[str, str] = {}
    for line in geom.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            values[key] = val
    return values


def _run_quiet(cmd: list[str], *, display: str, timeout: float = 3.0) -> str:
    env = dict(os.environ)
    env["DISPLAY"] = display
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
