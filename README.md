# raisim-visualizer-manager

Config-driven wrapper for RaiSim visual evaluation workflows.

It launches or positions RaiSimUnity, records X11 windows, runs a configured
tester command, and optionally uploads artifacts to Discord. Environment-specific
rollout logic stays in your tester.

## Install

```bash
python3 -m pip install -e .
```

## Dry Run

```bash
python3 -m raisim_visualizer_manager.cli \
  --config examples/generic_tester.yaml \
  --dry-run
```

After installation, the console script is also available:

```bash
raisim-visualizer-manager \
  --config examples/generic_tester.yaml \
  --dry-run
```

## Run A Tester

```bash
python3 -m raisim_visualizer_manager.cli \
  --config examples/generic_tester.yaml
```

For bolt-wrench grasp iteration, start from:

```bash
python3 -m raisim_visualizer_manager.cli \
  --config examples/bolt_wrench_visual_eval.yaml \
  --set checkpoint=/path/to/full_299.pt
```

## Config Model

- `vars`: reusable paths and run values
- `tester`: command, cwd, env, timeout
- `unity`: Unity launch, GUI port rewrite, display, window placement
- `recording`: wrapper-owned X11 recording
- `opencv`: optional rectangle recording for externally-created OpenCV windows
- `discord`: webhook discovery and upload file list

Use `DISCORD_WEBHOOK_URL` for secrets. Do not commit webhook URLs.

## CI

GitHub Actions runs the unit tests, `compileall`, a generic dry-run, and a
generic tester smoke on Python 3.10, 3.11, and 3.12.
