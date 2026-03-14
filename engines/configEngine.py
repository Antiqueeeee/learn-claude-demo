from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_default_base_url : str = Field(..., alias="LLM_DEFAULT_BASE_URL")
    llm_default_api_key : str = Field(..., alias="LLM_DEFAULT_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",              # 自动读取 .env（本地开发）
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",               # .env 里多余的变量不报错（你也可以改成 "forbid" 更严格）
    )

@lru_cache
def get_settings() -> Settings:
    # 缓存：全局只创建一次，避免到处重复解析
    return Settings()

SETTINGS = get_settings()