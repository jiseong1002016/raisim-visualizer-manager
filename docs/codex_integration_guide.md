# Codex Integration Guide

Use this checklist when adding the visualizer wrapper to a new RaiSim project.

1. Identify the real tester command first. It should run without this wrapper.
2. Put every project-specific path in `vars` in a YAML file.
3. Set `tester.cwd` to the project directory where relative tester paths work.
4. Set `unity.port` to the same port used by the environment or tester.
5. If the tester can launch Unity itself, disable `unity.launch` here to avoid
   two Unity processes.
6. If this wrapper launches Unity, ensure `unity.bin` and `unity.gui_settings`
   point to the local RaiSimUnity installation.
7. Keep `recording.enable` off when the tester already records video. Put the
   tester-generated video path in `discord.upload_files`.
8. Use `--dry-run` before a real run and inspect the rendered command.
9. Run one no-Discord local artifact test before enabling upload.

Required external tools for full visual mode:

- RaiSimUnity executable
- X11 display such as `:1`
- `xdotool` for window discovery and placement
- `ffmpeg` with x11grab support
- `curl` for Discord upload

The wrapper reports success of its orchestration, but the tester remains the
source of truth for policy correctness and environment-specific diagnostics.
