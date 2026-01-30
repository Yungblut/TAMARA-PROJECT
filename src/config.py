"""
TAMARA Configuration Module
Centralizes all system configuration.
Supports environment variables for sensitive credentials.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List

import yaml

# Load environment variables from .env file automatically
# If .env file doesn't exist, just continue
try:
    from dotenv import load_dotenv
    load_dotenv()  # Looks for .env in current directory
    print("[Config] .env file loaded successfully")
except ImportError:
    # If python-dotenv is not installed, use system environment variables
    pass


def get_env(key: str, default: str = "") -> str:
    """
    Get an environment variable with a default value.
    
    Args:
        key: Environment variable name.
        default: Default value if not found.
        
    Returns:
        Variable value or default.
    """
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get an environment variable as boolean.
    
    Args:
        key: Environment variable name.
        default: Default value.
        
    Returns:
        True if value is 'true', '1', 'yes' (case insensitive).
    """
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default


def get_env_int(key: str, default: int = 0) -> int:
    """
    Get an environment variable as integer.
    
    Args:
        key: Environment variable name.
        default: Default value.
        
    Returns:
        Integer value or default.
    """
    value = os.environ.get(key, "")
    try:
        return int(value) if value else default
    except ValueError:
        return default


@dataclass
class LLMConfig:
    """Language model configuration."""
    model: str = field(default_factory=lambda: get_env("TAMARA_LLM_MODEL", "gpt-oss:20b"))
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


@dataclass
class TTSConfig:
    """Text-to-Speech engine configuration."""
    model_path: str = "kokoro-models/kokoro-v1.0.onnx"
    voices_path: str = "kokoro-models/voices-v1.0.bin"
    voice: str = "ef_dora"
    speed: float = 1.1
    language: str = "es"


@dataclass
class ServerConfig:
    """Web server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"


@dataclass
class DatabaseConfig:
    """
    MariaDB connection configuration.
    
    Supports environment variables:
    - TAMARA_DB_HOST
    - TAMARA_DB_PORT
    - TAMARA_DB_USER
    - TAMARA_DB_PASSWORD
    - TAMARA_DB_NAME
    - TAMARA_DB_ALLOW_WRITE
    """
    enabled: bool = False
    host: str = field(default_factory=lambda: get_env("TAMARA_DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: get_env_int("TAMARA_DB_PORT", 3306))
    user: str = field(default_factory=lambda: get_env("TAMARA_DB_USER", "root"))
    password: str = field(default_factory=lambda: get_env("TAMARA_DB_PASSWORD", ""))
    database: str = field(default_factory=lambda: get_env("TAMARA_DB_NAME", ""))
    allow_write: bool = field(default_factory=lambda: get_env_bool("TAMARA_DB_ALLOW_WRITE", False))


@dataclass
class ToolsConfig:
    """Tools system configuration."""
    enabled: bool = True
    available: List[str] = field(default_factory=lambda: [
        "list_database_tables",
        "describe_table",
        "query_database",
        "get_table_count"
    ])


@dataclass
class Config:
    """Main TAMARA configuration."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    
    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """
        Load configuration from YAML file.
        If file doesn't exist, use default values.
        """
        config = cls()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                
                # LLM Config
                if 'llm' in data:
                    for key, value in data['llm'].items():
                        if hasattr(config.llm, key):
                            setattr(config.llm, key, value)
                
                # TTS Config
                if 'tts' in data:
                    for key, value in data['tts'].items():
                        if hasattr(config.tts, key):
                            setattr(config.tts, key, value)
                
                # Server Config
                if 'server' in data:
                    for key, value in data['server'].items():
                        if hasattr(config.server, key):
                            setattr(config.server, key, value)
                
                # Database Config
                if 'database' in data:
                    for key, value in data['database'].items():
                        if hasattr(config.database, key):
                            setattr(config.database, key, value)
                
                # Tools Config
                if 'tools' in data:
                    for key, value in data['tools'].items():
                        if hasattr(config.tools, key):
                            setattr(config.tools, key, value)
                            
            except Exception as e:
                print(f"[Config] Error loading config.yaml: {e}")
                print("[Config] Using default values")
        
        return config
    
    def save(self, config_path: str = "config.yaml") -> None:
        """Save current configuration to YAML file."""
        data = {
            'llm': {
                'model': self.llm.model,
                'max_history': self.llm.max_history,
                'system_prompt': self.llm.system_prompt,
            },
            'tts': {
                'model_path': self.tts.model_path,
                'voices_path': self.tts.voices_path,
                'voice': self.tts.voice,
                'speed': self.tts.speed,
                'language': self.tts.language,
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'reload': self.server.reload,
                'log_level': self.server.log_level,
            },
            'database': {
                'enabled': self.database.enabled,
                'host': self.database.host,
                'port': self.database.port,
                'user': self.database.user,
                'password': self.database.password,
                'database': self.database.database,
                'allow_write': self.database.allow_write,
            },
            'tools': {
                'enabled': self.tools.enabled,
                'available': self.tools.available,
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration instance (singleton)."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config() -> Config:
    """Reload configuration from file."""
    global _config
    _config = Config.load()
    return _config
