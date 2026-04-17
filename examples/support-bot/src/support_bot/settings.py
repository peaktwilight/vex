from __future__ import annotations

import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as exc:
    raise SystemExit("Install agent deps: uv sync --extra agent") from exc


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VEX_", env_file=".env", extra="ignore"
    )

    provider: str = "auto"
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"

    def resolve_provider(self) -> str:
        if self.provider != "auto":
            return self.provider
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        return "ollama"

    def model_spec(self) -> str:
        provider = self.resolve_provider()
        if provider == "openai":
            return f"openai:{self.openai_model}"
        if provider == "anthropic":
            return f"anthropic:{self.anthropic_model}"
        return f"openai:{self.ollama_model}"

    def is_local_fallback(self) -> bool:
        return self.resolve_provider() == "ollama"
