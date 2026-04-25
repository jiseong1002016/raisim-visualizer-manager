import subprocess
from pathlib import Path

from raisim_visualizer_manager import discord


def test_upload_files_uses_http_failure_status(monkeypatch, tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("x", encoding="utf-8")
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 22)

    monkeypatch.setattr(discord.subprocess, "run", fake_run)

    sent = discord.upload_files("https://discord.com/api/webhooks/bad/bad", [str(artifact)], "msg")

    assert sent is False
    assert "--fail-with-body" in captured["cmd"]


def test_upload_files_reports_success_on_zero_status(monkeypatch, tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("x", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(discord.subprocess, "run", fake_run)

    assert discord.upload_files("https://discord.com/api/webhooks/good/good", [str(artifact)], "msg") is True
