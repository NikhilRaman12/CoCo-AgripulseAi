"""
MCP Google Drive Tools
All Google Drive interactions go through this MCP interface.
"""

from __future__ import annotations

import os
import hashlib
import logging
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger("agripulse.mcp.gdrive")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_service():
    sa_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
    creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _get_folder_id() -> str:
    raw = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    if "folders/" in raw:
        return raw.split("folders/")[1].split("?")[0]
    return raw.strip()


def list_files(folder_id: str | None = None, mime_filter: str | None = None) -> list[dict[str, Any]]:
    """List all files in a Google Drive folder."""
    service = _get_service()
    fid = folder_id or _get_folder_id()
    query = f"'{fid}' in parents and trashed = false"
    if mime_filter:
        query += f" and mimeType='{mime_filter}'"

    files = []
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size, mimeType, modifiedTime)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    logger.info(f"Listed {len(files)} file(s) from folder {fid}")
    return files


def download_file(file_id: str, filename: str, dest_dir: str = "downloads") -> Path:
    """Download a file from Google Drive."""
    service = _get_service()
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    filepath = dest / filename

    request = service.files().get_media(fileId=file_id)
    with open(filepath, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    logger.info(f"Downloaded {filename} ({filepath.stat().st_size} bytes)")
    return filepath


def sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_file_metadata(file_id: str) -> dict[str, Any]:
    """Get metadata for a specific file."""
    service = _get_service()
    return service.files().get(
        fileId=file_id,
        fields="id, name, size, mimeType, modifiedTime, owners, permissions"
    ).execute()
