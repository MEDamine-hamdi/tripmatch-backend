from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de données
    DATABASE_URL: str = "sqlite:///./tripmatch.db"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Tokens email (US-02, US-04)
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Email
    # Email
    # Email
    EMAIL_PROVIDER: str = "console"  # "console" | "brevo"
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_SMTP_LOGIN: str = ""
    BREVO_SMTP_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "noreply@tripmatch.tn"
    BREVO_SENDER_NAME: str = "TripMatch"

    # Frontend (liens dans les emails)
    FRONTEND_URL: str = "https://tripmatch.app"

    ENVIRONMENT: str = "development"


settings = Settings()
