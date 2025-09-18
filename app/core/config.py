from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stocks-FundaAnalytics"
    API_V1_STR: str = "/api/v1"
    GOOGLE_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        ignore_extra = True

settings = Settings()