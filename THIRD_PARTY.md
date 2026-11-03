# Third-party components

FixVision integrates the following. None of them were built by us. Each keeps its own license; license files are kept wherever code is vendored.

| Component | Source | License | How we use it | Status |
|---|---|---|---|---|
| Meta Model API (Muse Spark 1.3, SAM 3.1, Muse Voice Transcribe) | https://dev.meta.ai | Meta Model API terms | Inference over HTTPS | Used |
| meta-sam-parser | https://pypi.org/project/meta-sam-parser/ (Meta Platforms) | SAM License | Parsing SAM 3.1 streamed segmentation records | Used |
| SQLModel | https://github.com/fastapi/sqlmodel | MIT | Job database tables | Used |
| python-multipart | https://github.com/Kludex/python-multipart | Apache-2.0 | Parsing clip uploads in FastAPI | Used |
| Playwright | https://github.com/microsoft/playwright | Apache-2.0 | Browser smoke test (dev only) | Used |
| OpenAI Python SDK | https://github.com/openai/openai-python | Apache-2.0 | HTTP client for the Meta Model API (OpenAI-compatible) | Used |
| Archify | https://github.com/tt-a1i/archify | Apache-2.0 | Architecture diagrams in docs (dev tool) | Dev only |
| FastAPI, Pydantic, Next.js, ffmpeg | Respective projects | MIT / BSD / LGPL (ffmpeg as external binary) | App framework, media processing | Used |

## Data and media

- All demo and evaluation videos are filmed by the author on the author's own rig.
- The pump guide in `data/guides/` is written by the author. No manufacturer manuals or copyrighted media are committed.
- No personal data is collected in the demo.

## Development tools (not part of the product)

Claude Code and Muse Code were used as coding assistants. All in-product AI runs on Meta models.
