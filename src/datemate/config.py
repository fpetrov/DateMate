from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv


class Settings(BaseSettings):
    bot_token: str = Field(...)
    redis_url: str = Field(...)
    database_url: str = Field(...)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def load_settings() -> Settings:
    load_dotenv()
    return Settings()
