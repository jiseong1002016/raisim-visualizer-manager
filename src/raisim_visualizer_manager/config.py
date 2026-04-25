from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when the visualizer config is missing required fields."""


class _MissingDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def load_config(path: str | os.PathLike[str], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"top-level config must be a mapping: {config_path}")

    cfg = dict(loaded)
    cfg.setdefault("vars", {})
    cfg["vars"].setdefault("config_dir", str(config_path.parent))
    cfg["vars"].setdefault("cwd", os.getcwd())
    if overrides:
        cfg["vars"].update({k: v for k, v in overrides.items() if v is not None})
    return render_templates(cfg)


def render_templates(value: Any, context: dict[str, Any] | None = None) -> Any:
    if context is None:
        context = value if isinstance(value, dict) else {}
    if isinstance(value, dict):
        rendered = {k: render_templates(v, context) for k, v in value.items()}
        if value is context:
            # A second pass lets fields reference other rendered fields.
            rendered = {k: render_templates(v, rendered) for k, v in rendered.items()}
        return rendered
    if isinstance(value, list):
        return [render_templates(v, context) for v in value]
    if isinstance(value, str):
        return _format_string(value, context)
    return value


def command_from_config(cfg: dict[str, Any]) -> list[str]:
    tester = cfg.get("tester", {})
    command = tester.get("command")
    if not isinstance(command, list) or not command:
        raise ConfigError("tester.command must be a non-empty list")
    return [str(part) for part in command]


def env_from_config(cfg: dict[str, Any]) -> dict[str, str]:
    env = dict(os.environ)
    configured = cfg.get("tester", {}).get("env", {})
    if configured:
        if not isinstance(configured, dict):
            raise ConfigError("tester.env must be a mapping")
        env.update({str(k): str(v) for k, v in configured.items()})
    display = cfg.get("unity", {}).get("display")
    if display:
        env["DISPLAY"] = str(display)
    return env


def output_paths(cfg: dict[str, Any]) -> list[str]:
    upload = cfg.get("discord", {}).get("upload_files", [])
    if not isinstance(upload, list):
        raise ConfigError("discord.upload_files must be a list")
    return [str(path) for path in upload]


def _format_string(template: str, context: dict[str, Any]) -> str:
    flat = _flatten(context)
    missing = _MissingDict(flat)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(missing[key])

    return re.sub(r"\{([A-Za-z0-9_.-]+)\}", replace, template)


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        out[name] = item
        if isinstance(item, dict):
            out.update(_flatten(item, name))
    return out
