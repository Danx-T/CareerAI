import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CV Optimizer & Interview Coach"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = ""  # MUST be set via .env — generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Groq Cloud LLM
    GROQ_API_KEY: str = ""  # MUST be set via .env — get from https://console.groq.com/keys
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # File Upload
    MAX_FILE_SIZE_MB: int = 10

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# ─── Startup validation ──────────────────────────────────────────────────────
def _validate_settings():
    errors = []
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-super-secret-key-change-this-in-production":
        errors.append("SECRET_KEY is not set. Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\"")
    if not settings.GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set. Get one from https://console.groq.com/keys")
    if errors:
        for e in errors:
            print(f"❌ FATAL CONFIG ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)

_validate_settings()
