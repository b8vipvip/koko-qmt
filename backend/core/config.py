"""应用配置模块。"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """从环境变量或项目根目录 .env 文件读取后端基础配置。"""

    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    qmt_client_path: str = Field(default="", alias="QMT_CLIENT_PATH")
    qmt_account_id: str = Field(default="", alias="QMT_ACCOUNT_ID")
    qmt_account_type: str = Field(default="STOCK", alias="QMT_ACCOUNT_TYPE")
    trade_mode: str = Field(default="paper", alias="TRADE_MODE")
    enable_real_trade: bool = Field(default=False, alias="ENABLE_REAL_TRADE")
    postgres_host: str = Field(default="127.0.0.1", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="koko_qmt", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    database_url: str = Field(default="", alias="DATABASE_URL")

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        """DATABASE_URL 为空时，根据 POSTGRES_* 配置拼接连接串。"""

        if self.database_url.strip():
            return self

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        auth = f"{user}:{password}" if password else user
        self.database_url = (
            f"postgresql+psycopg2://{auth}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return self

    def get_database_url(self) -> str:
        """返回 SQLAlchemy PostgreSQL 连接串，优先使用 DATABASE_URL。"""

        return self.database_url

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """返回缓存后的配置对象，避免重复读取环境文件。"""

    return Settings()


settings = get_settings()
