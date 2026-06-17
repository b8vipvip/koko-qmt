"""应用配置模块。"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量或 .env 文件读取后端基础配置。"""

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

    def get_database_url(self) -> str:
        """返回 SQLAlchemy PostgreSQL 连接串，优先使用 DATABASE_URL。"""

        if self.database_url:
            return self.database_url

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        auth = f"{user}:{password}" if password else user
        return f"postgresql+psycopg2://{auth}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """返回缓存后的配置对象，避免重复读取环境文件。"""

    return Settings()


settings = get_settings()
