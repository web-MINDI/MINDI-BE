import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# 환경 변수로 UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'ko_KR.UTF-8'
os.environ['LC_ALL'] = 'ko_KR.UTF-8'

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    AWS_REGION: str = "us-northeast-2"
    
    # 이메일 설정
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@mindi.com"
    FROM_NAME: str = "MINDI"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
