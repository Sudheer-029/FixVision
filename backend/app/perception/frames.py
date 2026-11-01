"""ffmpeg helpers: trim + sample a clip before SAM (SAM bills every frame it receives).
Resolution is kept: thin parts were only segmented reliably at full size.

Sampled frame k of a window starting at `start` sits at `start + k / fps` on the clip's
timeline, which is how SAM frame markers become seconds (spec §4.2).
"""

import json
import subprocess
from pathlib import Path


def _run(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def duration_s(path: str | Path) -> float:
    out = _run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    )
    return float(json.loads(out)["format"]["duration"])


def sample(
    src: str | Path,
    dst: str | Path,
    fps: float,
    start: float = 0.0,
    duration: float | None = None,
) -> Path:
    """H.264 MP4 of `src` from `start` (for `duration` s), resampled to `fps`, no audio."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    window = ["-t", f"{duration:.3f}"] if duration is not None else []
    _run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", *window, "-i", str(src)]
        + ["-vf", f"fps={fps}", "-an", "-c:v", "libx264"]
        + ["-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dst)]
    )
    return dst


def extract_audio(src: str | Path, dst: str | Path) -> Path:
    """Mono 16-bit 24 kHz WAV, the format Voice Transcribe accepts."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "24000"]
        + ["-c:a", "pcm_s16le", str(dst)]
    )
    return dst
