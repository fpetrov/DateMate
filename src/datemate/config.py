from pydantic import BaseSettings, Field
from dotenv import load_dotenv


class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    redis_url: str = Field(..., env="REDIS_URL")
    database_url: str = Field(..., env="DATABASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    load_dotenv()
    return Settings()
