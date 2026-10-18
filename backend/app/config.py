from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "CodeSense"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./codesense.db"

    # AI Service (Optional - Knowledge base is used if not provided)
    ai_api_key: Optional[str] = None
    api_key: Optional[str] = None
    ai_model: str = "gemini-2.5-flash"

    @property
    def effective_ai_key(self) -> Optional[str]:
        """Return either ai_api_key or api_key if set."""
        return self.ai_api_key or self.api_key

    # Server & CORS
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Java Compiler
    java_compiler_path: str = "javac"
    compilation_timeout_seconds: int = 10


settings = Settings()
