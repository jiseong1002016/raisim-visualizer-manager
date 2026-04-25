from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .config import command_from_config, env_from_config, load_config, output_paths
from .discord import find_webhook, upload_files
from .process import ensure_parent, run_command, terminate_process
from .recording import start_x11_recording
from .unity import configure_gui_port, launch_unity, position_window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a configured RaiSim tester with optional Unity recording and Discord upload.")
    parser.add_argument("--config", required=True, help="YAML config path.")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="Override config vars entries.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without launching processes.")
    args = parser.parse_args(argv)

    overrides = _parse_overrides(args.set)
    cfg = load_config(args.config, overrides)
    command = command_from_config(cfg)
    env = env_from_config(cfg)
    summary = _build_summary(cfg, command)

    if args.dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    return run_visualizer(cfg, command, env)


def run_visualizer(cfg: dict, command: list[str], env: dict[str, str]) -> int:
    artifacts = cfg.get("artifacts", {})
    out_dir = str(artifacts.get("out_dir", "artifacts"))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    log_path = str(artifacts.get("log", str(Path(out_dir) / "visualizer.log")))
    ensure_parent(log_path)

    unity_cfg = cfg.get("unity", {})
    rec_cfg = cfg.get("recording", {})
    discord_cfg = cfg.get("discord", {})
    tester_cfg = cfg.get("tester", {})
    opencv_cfg = cfg.get("opencv", {})

    display = str(unity_cfg.get("display", env.get("DISPLAY", ":1")))
    width = int(unity_cfg.get("width", rec_cfg.get("width", 1280)))
    height = int(unity_cfg.get("height", rec_cfg.get("height", 720)))
    capture_offset = f"+{int(unity_cfg.get('window_x', 0))},{int(unity_cfg.get('window_y', 0))}"
    unity_proc = None
    record_proc = None
    opencv_record_proc = None

    with open(log_path, "a", encoding="utf-8") as log:
        try:
            if bool(unity_cfg.get("launch", False)):
                gui_settings = str(unity_cfg.get("gui_settings", ""))
                if gui_settings:
                    configured = configure_gui_port(gui_settings, int(unity_cfg.get("port", 8080)), out_dir)
                    _log(log, f"unity gui port configured={int(configured)}")
                unity_proc = launch_unity(
                    str(unity_cfg.get("bin", "")),
                    display,
                    width,
                    height,
                    str(Path(out_dir) / "raisimUnity.log"),
                )
                time.sleep(float(unity_cfg.get("launch_wait_sec", 8.0)))

            if bool(unity_cfg.get("position", True)):
                _, capture_offset, geom = position_window(
                    display=display,
                    pid=unity_proc.pid if unity_proc else None,
                    title_regex=str(unity_cfg.get("window_title_regex", "RaiSimUnity|RaiSim|raisim|Unity")),
                    x=int(unity_cfg.get("window_x", 0)),
                    y=int(unity_cfg.get("window_y", 0)),
                    width=width,
                    height=height,
                    attempts=int(unity_cfg.get("position_attempts", 30)),
                )
                _log(log, f"unity capture_offset={capture_offset} geometry={geom}")

            if bool(rec_cfg.get("enable", False)):
                record_proc = start_x11_recording(
                    ffmpeg_bin=str(rec_cfg.get("ffmpeg_bin", "ffmpeg")),
                    display=display,
                    capture_offset=capture_offset,
                    width=int(rec_cfg.get("width", width)),
                    height=int(rec_cfg.get("height", height)),
                    seconds=float(rec_cfg.get("seconds", 25.0)),
                    output=str(rec_cfg.get("output", str(Path(out_dir) / "unity.mp4"))),
                    crf=int(rec_cfg.get("crf", 28)),
                )

            if bool(opencv_cfg.get("capture_enable", False)):
                opencv_offset = f"+{int(opencv_cfg.get('window_x', 0))},{int(opencv_cfg.get('window_y', 0))}"
                opencv_record_proc = start_x11_recording(
                    ffmpeg_bin=str(rec_cfg.get("ffmpeg_bin", "ffmpeg")),
                    display=display,
                    capture_offset=opencv_offset,
                    width=int(opencv_cfg.get("width", 600)),
                    height=int(opencv_cfg.get("height", 372)),
                    seconds=float(opencv_cfg.get("seconds", rec_cfg.get("seconds", 25.0))),
                    output=str(opencv_cfg.get("output", str(Path(out_dir) / "opencv.mp4"))),
                    crf=int(opencv_cfg.get("crf", 28)),
                )

            _log(log, "running tester command: " + " ".join(command))
            code = run_command(
                command,
                cwd=str(tester_cfg.get("cwd", "")) or None,
                env=env,
                timeout=float(tester_cfg["timeout_sec"]) if tester_cfg.get("timeout_sec") is not None else None,
                log=log,
            )
            _log(log, f"tester exit_code={code}")

            recording_failed = False
            for proc in (record_proc, opencv_record_proc):
                if proc is not None:
                    if proc.wait() != 0:
                        recording_failed = True

            if code != 0:
                print(
                    "[raisim-visualizer-manager] FAIL "
                    f"tester_exit_code={code} recording={int(bool(rec_cfg.get('enable', False)))} "
                    f"discord_upload_sent=0 log={log_path}"
                )
                return int(code)

            missing_outputs = _missing_recording_outputs(rec_cfg, opencv_cfg)
            if recording_failed or missing_outputs:
                detail = ",".join(missing_outputs) if missing_outputs else "ffmpeg_exit"
                _log(log, f"recording failed detail={detail}")
                print(
                    "[raisim-visualizer-manager] FAIL "
                    f"tester_exit_code={code} recording={int(bool(rec_cfg.get('enable', False)))} "
                    f"discord_upload_sent=0 recording_error={detail} log={log_path}"
                )
                return 125

            upload_sent = False
            if bool(discord_cfg.get("enable", False)):
                webhook = find_webhook(
                    explicit=discord_cfg.get("webhook"),
                    env_var=str(discord_cfg.get("webhook_env", "DISCORD_WEBHOOK_URL")),
                    webhook_file=str(discord_cfg.get("webhook_file", "")),
                )
                upload_sent = upload_files(
                    webhook,
                    output_paths(cfg),
                    str(discord_cfg.get("message", "RaiSim visual evaluation complete.")),
                )
            print(
                "[raisim-visualizer-manager] OK "
                f"tester_exit_code={code} recording={int(bool(rec_cfg.get('enable', False)))} "
                f"discord_upload_sent={int(upload_sent)} log={log_path}"
            )
            return int(code)
        finally:
            terminate_process(record_proc)
            terminate_process(opencv_record_proc)
            terminate_process(unity_proc)


def _parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--set expects KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        overrides[key] = value
    return overrides


def _build_summary(cfg: dict, command: list[str]) -> dict:
    return {
        "tester_command": command,
        "tester_cwd": cfg.get("tester", {}).get("cwd", ""),
        "unity": cfg.get("unity", {}),
        "recording": cfg.get("recording", {}),
        "opencv": cfg.get("opencv", {}),
        "discord": {
            key: val for key, val in cfg.get("discord", {}).items()
            if key not in {"webhook"}
        },
    }


def _missing_recording_outputs(rec_cfg: dict, opencv_cfg: dict) -> list[str]:
    expected = []
    if bool(rec_cfg.get("enable", False)):
        expected.append(str(rec_cfg.get("output", "")))
    if bool(opencv_cfg.get("capture_enable", False)):
        expected.append(str(opencv_cfg.get("output", "")))
    return [path for path in expected if path and not Path(path).expanduser().is_file()]


def _log(log, msg: str) -> None:
    print(f"[raisim-visualizer-manager] {msg}", file=log, flush=True)


if __name__ == "__main__":
    sys.exit(main())
