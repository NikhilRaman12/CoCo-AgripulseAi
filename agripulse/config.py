"""
AgriPulse Configuration
Environment-based config with secure credential handling.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class SnowflakeConfig:
    account: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    user: str = os.getenv("SNOWFLAKE_USER", "")
    role: str = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    warehouse: str = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    database: str = os.getenv("SNOWFLAKE_DATABASE", "AGRIPULSE")
    schema: str = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
    stage: str = os.getenv("SNOWFLAKE_STAGE", "AGRI_DRIVE_STAGE")
    private_key_path: str = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "")
    token_file: str = os.getenv("SNOWFLAKE_TOKEN_FILE_PATH", "/snowflake/session/token")


@dataclass
class GoogleDriveConfig:
    service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
    folder_id: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")


@dataclass
class AgentConfig:
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    timeout_seconds: float = 120.0
    enable_memory: bool = True
    enable_trace: bool = True
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class MCPConfig:
    snowflake: SnowflakeConfig = field(default_factory=SnowflakeConfig)
    google_drive: GoogleDriveConfig = field(default_factory=GoogleDriveConfig)
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    market_api_key: str = os.getenv("MARKET_API_KEY", "")


@dataclass
class PlatformConfig:
    mcp: MCPConfig = field(default_factory=MCPConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    llm_model: str = os.getenv("LLM_MODEL", "snowflake-arctic")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "snowflake-arctic-embed-m")
