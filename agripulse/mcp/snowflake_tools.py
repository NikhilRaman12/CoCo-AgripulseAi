"""
MCP Snowflake Tools
All Snowflake interactions go through this MCP interface.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

import snowflake.connector

logger = logging.getLogger("agripulse.mcp.snowflake")


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Secure Snowflake connection — session token or key-pair."""
    base = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "AGRIPULSE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
    }

    token_path = Path(os.getenv("SNOWFLAKE_TOKEN_FILE_PATH", "/snowflake/session/token"))
    if token_path.exists():
        base["authenticator"] = "oauth"
        base["token"] = token_path.read_text().strip()
        return snowflake.connector.connect(**base)

    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "")
    if key_path and Path(key_path).exists():
        from cryptography.hazmat.primitives import serialization
        with open(key_path, "rb") as f:
            pk = serialization.load_pem_private_key(f.read(), password=None)
        base["private_key"] = pk.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        return snowflake.connector.connect(**base)

    raise RuntimeError("No secure Snowflake auth available.")


def query(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """Execute SQL and return results as list of dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def execute(sql: str, params: tuple | None = None) -> None:
    """Execute SQL without returning results."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
    finally:
        conn.close()


def upload_to_stage(local_path: str, stage: str, subdir: str = "") -> str:
    """PUT a file to an internal stage."""
    conn = get_connection()
    try:
        target = f"@{stage}/{subdir}" if subdir else f"@{stage}"
        cur = conn.cursor()
        cur.execute(f"PUT 'file://{local_path}' '{target}' AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
        logger.info(f"Uploaded {local_path} → {target}")
        return target
    finally:
        conn.close()


def list_stage_files(stage: str, pattern: str = "") -> list[dict[str, Any]]:
    """List files in a stage."""
    sql = f"LIST @{stage}"
    if pattern:
        sql += f" PATTERN='{pattern}'"
    return query(sql)


def get_table_schema(table: str) -> list[dict[str, Any]]:
    """Get column metadata for a table."""
    return query(f"DESCRIBE TABLE {table}")


def table_exists(table: str) -> bool:
    """Check if a table exists."""
    try:
        query(f"SELECT 1 FROM {table} LIMIT 0")
        return True
    except Exception:
        return False
