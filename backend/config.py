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
    glm_api_key: str = ""

    # Model configuration
    default_model: str = "deepseek-v4-pro"
    fallback_model: str = "glm-4-plus"

    # DeepSeek configuration
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-v4-pro"

    # GLM (Zhipu AI) configuration
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    glm_model: str = "glm-4-plus"

    # Workflow configuration
    max_review_iterations: int = 5
    max_llm_retries: int = 3
    code_execution_timeout: int = 30

    # Docker sandbox configuration
    use_docker_sandbox: bool = False
    sandbox_container_name: str = "devagent-sandbox"
    sandbox_image: str = "devagent-sandbox:latest"
    sandbox_workspace: str = "/workspace"

    # Code generation
    default_language: str = "python"


# Global settings instance
settings = Settings()
