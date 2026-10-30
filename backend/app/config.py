from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env lives at the repo root; extra keys are ignored so new vars never break startup
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    model_api_base_url: str = "https://api.meta.ai/v1"
    model_api_key: str = ""
    reasoning_model: str = "muse-spark-1.3"
    reasoning_model_eval: str = "muse-spark-1.3-contributor"
    segmentation_model: str = "sam-3.1"
    sam_sample_fps: float = 3.0
    daily_spend_limit_usd: float = 10.0

    baseten_api_key: str = ""
    baseten_model: str = "meta-models/muse-spark-open-1026"
    fireworks_api_key: str = ""
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    fireworks_base_model: str = ""

    guard_enabled: bool = True
    media_retention_days: int = 7
    rig_baseline_path: str = "../config/rig_baseline.yaml"


settings = Settings()
