from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://earp:earp@localhost:5432/earp"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
