from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    AWS_REGION: str = "us-northeast-2"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
