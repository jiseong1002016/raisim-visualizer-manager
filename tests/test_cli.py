import json
import os
import subprocess
import sys
from pathlib import Path


def test_dry_run_outputs_rendered_plan():
    root = Path(__file__).resolve().parents[1]
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "raisim_visualizer_manager.cli",
            "--config",
            str(root / "examples" / "generic_tester.yaml"),
            "--dry-run",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    payload = json.loads(res.stdout)
    assert payload["tester_command"][0] == "python3"
    assert payload["unity"]["launch"] is False


def test_generic_tester_executes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "raisim_visualizer_manager.cli",
            "--config",
            str(root / "examples" / "generic_tester.yaml"),
            "--set",
            f"out_dir={tmp_path}",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "tester_exit_code=0" in res.stdout
    assert (tmp_path / "visualizer.log").is_file()


def test_failed_tester_reports_fail(tmp_path):
    config = tmp_path / "fail.yaml"
    config.write_text(
        """
vars:
  out_dir: "{tmp}/artifacts"
artifacts:
  out_dir: "{{vars.out_dir}}"
  log: "{{vars.out_dir}}/visualizer.log"
tester:
  timeout_sec: 10
  command:
    - "{python}"
    - "-c"
    - "raise SystemExit(7)"
unity:
  launch: false
  position: false
recording:
  enable: false
opencv:
  capture_enable: false
discord:
  enable: false
  upload_files: []
""".format(tmp=tmp_path, python=sys.executable),
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, "-m", "raisim_visualizer_manager.cli", "--config", str(config)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert res.returncode == 7
    assert "[raisim-visualizer-manager] FAIL tester_exit_code=7" in res.stdout


def test_missing_discord_webhook_skips_upload(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("upload candidate", encoding="utf-8")
    config = tmp_path / "missing_webhook.yaml"
    config.write_text(
        """
vars:
  out_dir: "{tmp}/artifacts"
artifacts:
  out_dir: "{{vars.out_dir}}"
  log: "{{vars.out_dir}}/visualizer.log"
tester:
  timeout_sec: 10
  command:
    - "{python}"
    - "-c"
    - "print('tester ok')"
unity:
  launch: false
  position: false
recording:
  enable: false
opencv:
  capture_enable: false
discord:
  enable: true
  webhook_env: RAISIM_VISUALIZER_TEST_MISSING_WEBHOOK
  webhook_file: "{missing_file}"
  message: "should skip upload"
  upload_files:
    - "{artifact}"
""".format(
            tmp=tmp_path,
            python=sys.executable,
            missing_file=tmp_path / "no_webhook.txt",
            artifact=artifact,
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("RAISIM_VISUALIZER_TEST_MISSING_WEBHOOK", None)

    res = subprocess.run(
        [sys.executable, "-m", "raisim_visualizer_manager.cli", "--config", str(config)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "tester_exit_code=0" in res.stdout
    assert "discord_upload_sent=0" in res.stdout


def test_tester_timeout_reports_124(tmp_path):
    config = tmp_path / "timeout.yaml"
    config.write_text(
        """
vars:
  out_dir: "{tmp}/artifacts"
artifacts:
  out_dir: "{{vars.out_dir}}"
  log: "{{vars.out_dir}}/visualizer.log"
tester:
  timeout_sec: 0.2
  command:
    - "{python}"
    - "-c"
    - "import time; time.sleep(5)"
unity:
  launch: false
  position: false
recording:
  enable: false
opencv:
  capture_enable: false
discord:
  enable: false
  upload_files: []
""".format(tmp=tmp_path, python=sys.executable),
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, "-m", "raisim_visualizer_manager.cli", "--config", str(config)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert res.returncode == 124
    assert "[raisim-visualizer-manager] FAIL tester_exit_code=124" in res.stdout


def test_missing_unity_binary_fails_before_tester(tmp_path):
    marker = tmp_path / "tester_marker.txt"
    config = tmp_path / "missing_unity.yaml"
    config.write_text(
        """
vars:
  out_dir: "{tmp}/artifacts"
artifacts:
  out_dir: "{{vars.out_dir}}"
  log: "{{vars.out_dir}}/visualizer.log"
tester:
  timeout_sec: 10
  command:
    - "{python}"
    - "-c"
    - "from pathlib import Path; Path(r'{marker}').write_text('ran')"
unity:
  launch: true
  position: false
  bin: "{missing_bin}"
  display: ":1"
  width: 320
  height: 240
  launch_wait_sec: 0
recording:
  enable: false
opencv:
  capture_enable: false
discord:
  enable: false
  upload_files: []
""".format(
            tmp=tmp_path,
            python=sys.executable,
            marker=marker,
            missing_bin=tmp_path / "missing_raisimUnity",
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, "-m", "raisim_visualizer_manager.cli", "--config", str(config)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert res.returncode != 0
    assert "Unity binary not found" in res.stderr
    assert not marker.exists()


def test_missing_recording_output_reports_failure(tmp_path):
    config = tmp_path / "recording_fail.yaml"
    config.write_text(
        """
vars:
  out_dir: "{tmp}/artifacts"
artifacts:
  out_dir: "{{vars.out_dir}}"
  log: "{{vars.out_dir}}/visualizer.log"
tester:
  timeout_sec: 10
  command:
    - "{python}"
    - "-c"
    - "print('tester ok')"
unity:
  launch: false
  position: false
  display: ":254"
  window_x: 0
  window_y: 0
recording:
  enable: true
  ffmpeg_bin: ffmpeg
  width: 64
  height: 64
  seconds: 0.2
  output: "{{vars.out_dir}}/unity.mp4"
opencv:
  capture_enable: false
discord:
  enable: false
  upload_files: []
""".format(tmp=tmp_path, python=sys.executable),
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, "-m", "raisim_visualizer_manager.cli", "--config", str(config)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert res.returncode == 125
    assert "[raisim-visualizer-manager] FAIL tester_exit_code=0" in res.stdout
    assert "recording_error=" in res.stdout
