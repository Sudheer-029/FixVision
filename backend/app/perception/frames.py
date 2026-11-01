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


def for_model(src: str | Path, dst: str | Path) -> Path:
    """720p H.264 MP4 with mono audio for Muse Spark (it reads embedded audio too)."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=-2:720", "-c:v", "libx264"]
        + [
            "-crf",
            "26",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-ac",
            "1",
            "-movflags",
            "+faststart",
        ]
        + [str(dst)]
    )
    return dst


def crop_frames(
    src: str | Path, box: tuple[float, float, float, float], out_dir: str | Path, fps: float = 1.0
) -> list[Path]:
    """JPEG frames of `box` (padded 15%) at `fps`; frame i sits at i / fps seconds."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f*.jpg"):
        old.unlink()
    x1, y1, x2, y2 = box
    pad_w, pad_h = 0.15 * (x2 - x1), 0.15 * (y2 - y1)
    x, y = max(0, x1 - pad_w), max(0, y1 - pad_h)
    w, h = (x2 - x1) + 2 * pad_w, (y2 - y1) + 2 * pad_h
    crop = f"crop=min({w:.0f}\\,iw-{x:.0f}):min({h:.0f}\\,ih-{y:.0f}):{x:.0f}:{y:.0f}"
    _run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", f"fps={fps},{crop}", "-q:v", "3"]
        + [str(out_dir / "f%04d.jpg")]
    )
    return sorted(out_dir.glob("f*.jpg"))
