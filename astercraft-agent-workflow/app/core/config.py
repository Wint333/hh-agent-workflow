from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AsterCraft Agent Workflow"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    api_v1_prefix: str = "/api"
    database_url: str = "runtime/tmp/astercraft_agent.db"
    generated_image_dir: str = "runtime/tmp/generated_images"
    public_base_url: str = "http://127.0.0.1:8000"

    chat_provider: str = "mock"
    chat_api_key: str = ""
    chat_base_url: str = ""
    chat_model: str = ""

    image_provider: str = "mock"
    image_api_key: str = ""
    image_base_url: str = ""
    image_model: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def db_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path(self.database_url)

    @property
    def image_dir_path(self) -> Path:
        return Path(self.generated_image_dir)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.image_dir_path.mkdir(parents=True, exist_ok=True)
    return settings
