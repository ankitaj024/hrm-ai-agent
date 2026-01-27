from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    MONGODB_URL: str
    DB_NAME: str = "hrm-ai-agent"
    
    # SMTP Configuration (Optional for now)
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    # Google Calendar Configuration
    GOOGLE_SERVICE_ACCOUNT_JSON: str = "" # JSON content or path
    GOOGLE_CALENDAR_ID: str = "primary"

    # JWT Configuration
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Change in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300 # 5 hours for dev convenience

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

settings = Settings()
