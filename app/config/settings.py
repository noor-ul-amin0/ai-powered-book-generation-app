from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/book_generator"
    LLM_PROVIDER: str = "groq"  # groq, openai, anthropic, etc.
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: Optional[str] = None
    STORAGE_PROVIDER: str = "local"  # local, cloudinary, etc.
    LOCAL_STORAGE_PATH: str = "./storage"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
