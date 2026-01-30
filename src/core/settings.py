from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    """
    Centralized Configuration for CloudCull.
    Reads from environment variables (case-insensitive) and .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    # General
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = Field('INFO', alias='LOG_LEVEL')
    environment: Literal['development', 'production'] = Field('development', alias='cull_env')
    
    # Cloud Configs
    aws_region: str = Field('us-east-1', alias='AWS_REGION')
    azure_subscription_id: str | None = Field(None, alias='AZURE_SUBSCRIPTION_ID')
    gcp_project_id: str | None = Field(None, alias='GCP_PROJECT_ID')
    
    # LLM Configs
    llm_provider: Literal['anthropic', 'openai', 'google', 'groq'] = Field('anthropic', alias='LLM_PROVIDER')
    anthropic_api_key: str | None = Field(None, alias='ANTHROPIC_API_KEY')
    openai_api_key: str | None = Field(None, alias='OPENAI_API_KEY')
    google_api_key: str | None = Field(None, alias='GOOGLE_API_KEY')
    groq_api_key: str | None = Field(None, alias='GROQ_API_KEY')
    
    # Dashboard
    dashboard_port: int = Field(5173, alias='DASHBOARD_PORT')
    metrics_port: int = Field(8000, alias='METRICS_PORT')

settings = Settings()
