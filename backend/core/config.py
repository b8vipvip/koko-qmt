"""应用配置模块。"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量或 .env 文件读取后端基础配置。"""

    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    trade_mode: str = Field(default="paper", alias="TRADE_MODE")
    enable_real_trade: bool = Field(default=False, alias="ENABLE_REAL_TRADE")

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
