from __future__ import annotations

import subprocess

from .process import ensure_parent


def start_x11_recording(
    *,
    ffmpeg_bin: str,
    display: str,
    capture_offset: str,
    width: int,
    height: int,
    seconds: float,
    output: str,
    crf: int = 28,
) -> subprocess.Popen:
    ensure_parent(output)
    return subprocess.Popen(
        [
            ffmpeg_bin,
            "-y",
            "-video_size", f"{int(width)}x{int(height)}",
            "-framerate", "30",
            "-f", "x11grab",
            "-i", f"{display}{capture_offset}",
            "-t", f"{float(seconds):.3f}",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", str(int(crf)),
            "-pix_fmt", "yuv420p",
            output,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
