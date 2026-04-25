from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def find_webhook(*, explicit: str | None = None, env_var: str = "DISCORD_WEBHOOK_URL", webhook_file: str = "") -> str:
    if explicit:
        return explicit
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    if webhook_file and Path(webhook_file).expanduser().is_file():
        text = Path(webhook_file).expanduser().read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"https://discord(?:app)?\.com/api/webhooks/\S+", text)
        if match:
            return match.group(0).rstrip(')"\'<>')
    return ""


def upload_files(webhook: str, files: list[str], content: str) -> bool:
    paths = [Path(p).expanduser() for p in files if p and Path(p).expanduser().is_file()]
    if not webhook or not paths:
        return False
    escaped = content.replace("\\", "\\\\").replace('"', '\\"')
    cmd = ["curl", "-sS", "-F", f'payload_json={{"content":"{escaped}"}}']
    for idx, path in enumerate(paths):
        cmd.extend(["-F", f"files[{idx}]=@{path}"])
    cmd.append(webhook)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0
