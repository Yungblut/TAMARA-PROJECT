"""
TAMARA Configuration Module
Type-safe configuration using Pydantic Settings.
Loads from config.yaml + environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Language model configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_LLM_")

    model: str = "qwen2.5:32b"
    max_history: int = 500
    system_prompt: str = (
        "You are TAMARA, an intelligent voice assistant with access to tools. "
        "Respond in Spanish in a conversational and brief manner. "
        "You have access to a MariaDB database. When the user asks about data, "
        "use the available tools to query the database. "
        "First list the tables, then describe their structure if necessary, "
        "and finally execute the appropriate query. "
        "Maximum 50 words per response."
    )


class TTSSettings(BaseSettings):
    """Kokoro TTS engine configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_TTS_")

    model_path: str = "kokoro-models/kokoro-v1.0.onnx"
    voices_path: str = "kokoro-models/voices-v1.0.bin"
    voice: str = "ef_dora"
    speed: float = 1.1
    language: str = "es"

    @field_validator("speed")
    @classmethod
    def clamp_speed(cls, v: float) -> float:
        return max(0.5, min(2.0, v))


class STTSettings(BaseSettings):
    """faster-whisper STT configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_STT_")

    enabled: bool = True
    model_size: str = "large-v3-turbo"
    compute_type: str = "int8"
    language: str = "es"
    beam_size: int = 5
    vad_filter: bool = True
    idle_timeout: int = 30  # seconds before unloading model


class ServerSettings(BaseSettings):
    """Web server configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_SERVER_")

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"


class DatabaseSettings(BaseSettings):
    """MariaDB connection configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_DB_")

    enabled: bool = False
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: SecretStr = SecretStr("")
    database: str = ""
    allow_write: bool = False


class ToolsSettings(BaseSettings):
    """Tools system configuration."""

    model_config = SettingsConfigDict(env_prefix="TAMARA_TOOLS_")

    enabled: bool = True
    available: list[str] = [
        "list_database_tables",
        "describe_table",
        "query_database",
        "get_table_count",
    ]


class Settings(BaseSettings):
    """Main TAMARA configuration."""

    llm: LLMSettings = LLMSettings()
    tts: TTSSettings = TTSSettings()
    stt: STTSettings = STTSettings()
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()
    tools: ToolsSettings = ToolsSettings()

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML file, with env vars taking precedence."""
        yaml_data: dict[str, Any] = {}

        if Path(config_path).exists():
            with open(config_path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

        # Build sub-settings from YAML, env vars auto-override
        return cls(
            llm=LLMSettings(**(yaml_data.get("llm", {}))),
            tts=TTSSettings(**(yaml_data.get("tts", {}))),
            stt=STTSettings(**(yaml_data.get("stt", {}))),
            server=ServerSettings(**(yaml_data.get("server", {}))),
            database=DatabaseSettings(**(yaml_data.get("database", {}))),
            tools=ToolsSettings(**(yaml_data.get("tools", {}))),
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Load .env file
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    return Settings.from_yaml()
