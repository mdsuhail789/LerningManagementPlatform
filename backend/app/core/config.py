from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "lms_db"
    jwt_secret_key: str = "dev-only-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # Gemini (Google) for AI recommendations.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # SMTP for Forgot Password
    smtp_server: str | None = None
    smtp_port: int | None = 587
    smtp_username: str | None = None
    smtp_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
