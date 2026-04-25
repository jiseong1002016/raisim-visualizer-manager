# Visualizer Modularization Plan

## Goal

Extract the Unity/OpenCV recording and Discord upload workflow from
`tester/etc/visualize/run_visual_eval.py` into a standalone git repository that
can be cloned and used around a RaiSim tester command.

The extracted module must not own task-specific rollout logic. A project-specific
tester remains responsible for loading the environment, checkpoint, scaling, and
policy. The visualizer module owns process orchestration:

- optional RaiSimUnity launch and port configuration
- Unity window discovery, positioning, and X11 capture
- optional OpenCV window positioning/capture when the wrapped tester exposes it
- bounded tester command execution
- output artifact layout
- optional Discord upload

## Existing Boundary

The original implementation combined several concerns in one script:

- RaiSim environment construction and checkpoint rollout
- in-memory task config mutation for the bolt-wrench grasp setup
- RaiSimUnity launch and `gui_settings.xml` port rewrite
- `xdotool` window positioning
- `ffmpeg` screen recording
- OpenCV tactile heatmap creation
- Discord webhook discovery and upload

The standalone repository extracts only the generic orchestration pieces. The
project-specific rollout remains in the source workspace and can be called as a
configured tester command.

## Repository Layout

```text
raisim-visualizer-manager/
  README.md
  pyproject.toml
  src/raisim_visualizer_manager/
    __init__.py
    cli.py
    config.py
    discord.py
    process.py
    recording.py
    unity.py
  examples/
    bolt_wrench_visual_eval.yaml
    generic_recording.yaml
    generic_tester.yaml
  docs/
    codex_integration_guide.md
    tester_contract.md
  tests/
    test_cli.py
    test_config.py
    test_discord.py
```

## Config Contract

All machine-specific and run-specific values live in YAML:

- tester command, working directory, environment variables, timeout
- checkpoint path and other named variables interpolated into the command
- Unity binary, `gui_settings.xml`, display, port, launch toggle, window size
- recording toggle, ffmpeg path, duration, output directory
- OpenCV toggle and optional capture rectangle
- Discord toggle, webhook env var, webhook file, upload file list, message

The wrapper supports both:

1. a generic tester that only needs Unity to be up while it runs
2. a richer tester that accepts flags for OpenCV and its output video path

## Implementation Sequence

1. Create standalone repo skeleton and CLI.
2. Implement config loading and variable interpolation.
3. Extract Unity process launch, GUI port rewrite, window positioning, and cleanup.
4. Extract ffmpeg X11 capture for Unity and optional OpenCV windows.
5. Implement generic tester subprocess wrapper with log capture and timeout.
6. Implement Discord upload helper.
7. Add examples for bolt-wrench `run_visual_eval.py` and generic testers.
8. Add docs for Codex agents explaining prerequisites and integration choices.
9. Add tests that avoid real Unity/ffmpeg by validating config, command
   rendering, dry-run execution, timeout, recording failure, and Discord failure.
10. Validate from a fresh clone and wire this workspace to call it through config
    without changing the working tester behavior.

## Non-Goals

- Do not move bolt-wrench reward, observation, checkpoint, or tactile heatmap
  computation into the standalone repo.
- Do not require Discord. Missing webhook leaves artifacts locally and reports
  that upload was skipped.
- Do not assume a specific tester path. The tester is a command template.

## Validation

Minimum validation before considering the module usable:

- `python -m pytest` passes in the standalone repo.
- `raisim-visualizer-manager --config examples/generic_tester.yaml --dry-run`
  renders the expected tester, Unity, ffmpeg, and Discord actions.
- bolt-wrench example config renders the same effective command line as the
  current `tester/etc/visualize/run_visual_eval.py` visual path.
- a no-Unity generic tester can execute.
- wrapper-owned X11 recording can create an mp4.
- missing webhook, bad webhook, tester timeout, missing Unity binary, and
  recording failure are reported explicitly.

Real visual validation:

- launch Unity on a configured display
- record Unity mp4
- write OpenCV tactile mp4 when the tester exposes it
- send generated files to Discord when a webhook is configured
