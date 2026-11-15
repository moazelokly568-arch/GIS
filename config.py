from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Geo Surveying AI Backend"
    ENVIRONMENT: str = "production"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    JWT_SECRET_KEY: str = "CHANGE_ME_TO_STRONG_64_CHAR_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./geomasaha_ai.db"
    ALLOWED_ORIGINS: List[str] = [
        "https://moazelokly568-arch.github.io",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]
    MAX_UPLOAD_MB: int = 15
    UPLOAD_DIR: str = "./storage/uploads"
    ARTIFACTS_DIR: str = "./storage/artifacts"
    ODA_CONVERTER_PATH: str = ""

    FREE_DAILY_REQUESTS: int = 10
    PRO_DAILY_REQUESTS: int = 200
    FREE_MAX_FILE_MB: int = 5
    PRO_MAX_FILE_MB: int = 15

    PAYMENT_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
