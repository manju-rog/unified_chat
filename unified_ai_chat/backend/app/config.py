"""Application configuration utilities."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration derived from environment variables."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    absence_api_base: AnyHttpUrl = Field("http://localhost:8010/api", env="ABSENCE_API_URL")

    sow_project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3] / "sow_gen_ai",
        env="SOW_PROJECT_PATH",
    )
    sow_default_template: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
        / "sow_gen_ai"
        / "G-COP SOW v1.0_CLEAN.docx",
        env="SOW_TEMPLATE_PATH",
    )
    sow_output_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent / ".." / "generated_docs",
        env="SOW_OUTPUT_DIR",
    )

    session_expiry_minutes: int = Field(60, env="SESSION_EXPIRY_MINUTES")
    session_history_limit: int = Field(10, env="SESSION_HISTORY_LIMIT")

    @validator("gemini_api_key")
    def _validate_key(cls, value: str) -> str:
        if not value:
            raise ValueError("GEMINI_API_KEY must be provided")
        return value

    @validator("sow_default_template")
    def _validate_template(cls, value: Path) -> Path:
        # Temporarily disable validation to focus on absence management
        # if not value.exists():
        #     raise ValueError(f"Default SOW template not found at {value}")
        return value

    @validator("sow_project_root")
    def _validate_project_root(cls, value: Path) -> Path:
        # Temporarily disable validation to focus on absence management
        # if not value.exists():
        #     raise ValueError(f"SOW project path not found at {value}")
        return value

    @validator("sow_output_dir", pre=True, allow_reuse=True)
    def _prepare_output_dir(cls, value: Path) -> Path:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
