import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        if not self.secret_key or self.secret_key == "replace me":
            raise RuntimeError("JWT_SECRET_KEY is not set. Copy .env.example to .env.")

@lru_cache
def get_settings() -> Settings:
    return Settings()
