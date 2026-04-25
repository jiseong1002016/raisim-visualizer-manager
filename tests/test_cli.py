import json
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
