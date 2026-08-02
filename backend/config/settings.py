import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # AI
    anthropic_api_key: str

    # S3/MinIO
    s3_endpoint_url: str
    s3_public_url: str = "http://localhost:9000"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str = "flawnetic-evidence"
    s3_region: str = "us-east-1"

    # ZAP
    zap_host: str = "http://localhost:8090"
    zap_api_key: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Scan limits
    max_concurrent_scans_per_user: int = 2
    evidence_retention_days: int = 30

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        case_sensitive = False
        extra = "ignore"

settings = Settings()
