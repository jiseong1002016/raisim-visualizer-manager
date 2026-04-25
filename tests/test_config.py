from pathlib import Path

from raisim_visualizer_manager.config import command_from_config, load_config


def test_generic_config_renders_command():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "examples" / "generic_tester.yaml")

    command = command_from_config(cfg)

    assert command[:2] == ["python3", "-c"]
    assert cfg["artifacts"]["log"].endswith("artifacts/generic/visualizer.log")
    assert cfg["discord"]["upload_files"][0].endswith("artifacts/generic/unity.mp4")


def test_overrides_update_vars():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "examples" / "generic_tester.yaml", {"python": "/tmp/python"})

    assert command_from_config(cfg)[0] == "/tmp/python"


def test_bolt_wrench_config_delegates_rollout_and_uploads_artifacts():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "examples" / "bolt_wrench_visual_eval.yaml", {"checkpoint": "/tmp/full_1.pt"})
    command = command_from_config(cfg)

    assert "tester/etc/visualize/run_visual_eval.py" in command
    assert "/tmp/full_1.pt" in command
    assert "--no-launch-unity" in command
    assert "--no-discord-upload" in command
    assert cfg["unity"]["launch"] is True
    assert cfg["discord"]["upload_files"][0].endswith("unity.mp4")


def test_generic_recording_config_uses_wrapper_recording():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "examples" / "generic_recording.yaml")

    assert cfg["unity"]["launch"] is False
    assert cfg["recording"]["enable"] is True
    assert cfg["recording"]["output"].endswith("artifacts/generic_recording/unity.mp4")
