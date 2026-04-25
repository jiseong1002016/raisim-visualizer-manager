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
