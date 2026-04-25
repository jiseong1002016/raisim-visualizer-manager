# Tester Contract

`raisim-visualizer-manager` wraps a tester process. It does not load policy
checkpoints, mutate RaiSim task config, or implement environment-specific
rollouts.

The tester command should:

- exit with `0` on success and non-zero on failure
- accept all checkpoint, seed, horizon, and task options from CLI/config
- connect to the same RaiSimUnity port configured in the YAML when Unity is used
- write requested artifacts to deterministic paths
- flush useful logs to stdout/stderr so the wrapper log is sufficient for debug

For OpenCV, there are two supported patterns:

- Preferred: the tester writes its own OpenCV video artifact and the wrapper only
  uploads it.
- Generic: the tester opens a stable OpenCV window and the wrapper records a
  configured screen rectangle with `ffmpeg x11grab`.

For Discord, keep the webhook out of git. Use `DISCORD_WEBHOOK_URL` or a local
untracked file referenced by `discord.webhook_file`.
