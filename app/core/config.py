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

    # Tokens email
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Email
    EMAIL_PROVIDER: str = "console"  # "console" | "brevo"
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "matrixbeji1@gmail.com"
    BREVO_SENDER_NAME: str = "TripMatch"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Frontend
    FRONTEND_URL: str = "https://tripmatch.app"

    ENVIRONMENT: str = "development"


settings = Settings()