"""One real call per model; prints model, latency, usage and estimated cost.

Run from the repo root:  uv run --project backend python scripts/smoke.py
Uses the first MP4 in data/samples/ for the video call; otherwise (and for the image
and WAV) it generates small synthetic test media with ffmpeg into data/cache/smoke/.
Always bypasses the cache so the numbers are real.
"""

import json
import subprocess
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.clients.baseten_client import BasetenClient  # noqa: E402
from app.clients.meta_client import CallResult, MetaClient  # noqa: E402
from app.config import settings  # noqa: E402

OUT = REPO / "data" / "cache" / "smoke"


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def media() -> tuple[Path, Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = sorted((REPO / "data" / "samples").glob("*.mp4"))
    video = samples[0] if samples else OUT / "synthetic.mp4"
    if not samples and not video.exists():
        ffmpeg("-f", "lavfi", "-i", "testsrc=duration=3:size=640x480:rate=3",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video))  # fmt: skip
    image = OUT / "frame.png"
    if not image.exists():
        ffmpeg("-i", str(video), "-frames:v", "1", str(image))
    wav = OUT / "tone.wav"
    if not wav.exists():
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=3",
               "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(wav))  # fmt: skip
    return video, image, wav


def report(name: str, model: str, r: CallResult) -> None:
    print(f"OK   {name:<14} {model:<34} {r.latency_ms:>6} ms  ${r.cost_usd:.5f}")
    print(f"     usage {json.dumps(r.usage)}")
    print(f"     text  {r.text[:120]!r}")


def main() -> int:
    video, image, wav = media()
    meta = MetaClient()
    model = settings.reasoning_model
    calls = [
        ("text", model, lambda: meta.respond(model, "Reply with the word OK.", use_cache=False)),
        (
            "video",
            model,
            lambda: meta.respond(
                model,
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Describe this clip in one sentence."},
                            {"type": "input_video", "file_id": meta.upload_file(video)},
                        ],
                    }
                ],
                use_cache=False,
            ),
        ),
        (
            "sam image",
            settings.segmentation_model,
            lambda: meta.sam_segment(image, "rectangle", use_cache=False),
        ),
        ("voice", "muse-voice-transcribe-1.0", lambda: meta.transcribe(wav, use_cache=False)),
    ]
    if settings.baseten_api_key:
        bt = BasetenClient()
        calls.append(
            (
                "baseten",
                settings.baseten_model,
                lambda: bt.chat([{"role": "user", "content": "Reply with the word OK."}]),
            )
        )
    else:
        print("SKIP baseten (BASETEN_API_KEY not set)")

    failed = 0
    video_usage = None
    for name, m, call in calls:
        try:
            r = call()
            report(name, m, r)
            if name == "video":
                video_usage = r.usage
        except Exception as exc:
            failed += 1
            print(f"FAIL {name:<14} {m:<34} {type(exc).__name__}: {exc}")
            traceback.print_exc(limit=1)

    print(f"\nVIDEO TOKENS ({video.name}): {json.dumps(video_usage)}")
    print(f"Spent today (ledger): ${meta.ledger.spent_today():.4f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
