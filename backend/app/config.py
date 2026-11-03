from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # .env lives at the repo root; extra keys are ignored so new vars never break startup
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    model_api_base_url: str = "https://api.meta.ai/v1"
    model_api_key: str = ""
    reasoning_model: str = "muse-spark-1.3"
    segmentation_model: str = "sam-3.1"
    sam_sample_fps: float = 3.0
    daily_spend_limit_usd: float = 10.0

    rig_baseline_path: str = str(REPO_ROOT / "config" / "rig_baseline.yaml")
    cache_dir: Path = REPO_ROOT / "data" / "cache"
    ledger_path: Path = REPO_ROOT / "data" / "cache" / "ledger.sqlite"
    db_path: Path = REPO_ROOT / "data" / "private" / "fixvision.sqlite"
    jobs_dir: Path = REPO_ROOT / "data" / "private" / "jobs"  # uploaded media, git-ignored


settings = Settings()
