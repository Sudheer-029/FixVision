# Third-party components

FixVision integrates the following. None of them were built by us. Each keeps its own license; license files are kept wherever code is vendored.

| Component | Source | License | How we use it | Status |
|---|---|---|---|---|
| Meta Model API (Muse Spark 1.3, SAM 3.1, Muse Voice Transcribe, Muse Image) | https://dev.meta.ai | Meta Model API terms | Inference over HTTPS | Used |
| Muse Spark Open (open weights) | Baseten hosted inference (`meta-models/muse-spark-open-1026`) | Model license per Meta | Record drafting, eval backend | Planned |
| Fireworks AI | Fine-tuning and serving a Muse open-weight model | Fireworks terms; model license per Meta | Fine-tuned observation extractor, compared with the base model | Stretch |
| meta-sam-parser | https://pypi.org/project/meta-sam-parser/ (Meta Platforms) | SAM License | Parsing SAM 3.1 streamed segmentation records | Used |
| OpenAI Python SDK | https://github.com/openai/openai-python | Apache-2.0 | HTTP client for the Meta Model API (OpenAI-compatible) | Used |
| LlamaFirewall (PurpleLlama) | https://github.com/meta-llama/PurpleLlama | MIT (tools); guard models under the Llama Community License | Prompt-injection scanning of transcripts and documents | Planned |
| prompt-ops | https://github.com/meta-llama/prompt-ops | MIT | Prompt optimization against the trial set | Stretch |
| synthetic-data-kit | https://github.com/meta-llama/synthetic-data-kit | MIT | Drafting extra test questions from our own pump guide | Stretch |
| Meta-Harness | https://github.com/stanford-iris-lab/meta-harness | MIT | Harness search over the reasoning agent | Stretch |
| Archify | https://github.com/tt-a1i/archify | Apache-2.0 | Architecture diagrams in docs (dev tool) | Dev only |
| FastAPI, Pydantic, Next.js, ffmpeg | Respective projects | MIT / BSD / LGPL (ffmpeg as external binary) | App framework, media processing | Used |

## Data and media

- All demo and evaluation videos are filmed by the author on the author's own rig.
- The pump guide in `data/guides/` is written by the author. No manufacturer manuals or copyrighted media are committed.
- No personal data is collected in the demo.

## Development tools (not part of the product)

Claude Code and Muse Code were used as coding assistants. All in-product AI runs on Meta models.
