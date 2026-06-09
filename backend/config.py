"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "DevAgent Team"
    output_dir: str = "output"

    # LLM API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""

    # Model configuration
    default_model: str = "deepseek-v4-pro"
    fallback_model: str = "claude-3-5-sonnet-20241022"

    # DeepSeek configuration
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-v4-pro"

    # Workflow configuration
    max_review_iterations: int = 3
    max_llm_retries: int = 3
    code_execution_timeout: int = 30


# Global settings instance
settings = Settings()
