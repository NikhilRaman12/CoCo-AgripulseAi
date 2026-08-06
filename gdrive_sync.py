"""
AgriPulse: Google Drive → Snowflake Stage Sync
Downloads files from a Google Drive folder and uploads them to a Snowflake internal stage.
"""

import os
import io
import hashlib
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import snowflake.connector

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("gdrive_sync")

# --- Config ---
def get_folder_id(raw: str) -> str:
    """Extract folder ID from URL or raw string."""
    if "folders/" in raw:
        return raw.split("folders/")[1].split("?")[0]
    return raw.strip()

FOLDER_ID = get_folder_id(os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""))
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "downloads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "100")) * 1024 * 1024
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "").split(",")
STAGE_SUBDIR = os.getenv("STAGE_SUBDIRECTORY", "google_drive")
AUTO_DELETE = os.getenv("AUTO_DELETE_AFTER_UPLOAD", "true").lower() == "true"
ENABLE_DUPLICATE_CHECK = os.getenv("ENABLE_DUPLICATE_CHECK", "true").lower() == "true"
ENABLE_SHA256 = os.getenv("ENABLE_SHA256_VALIDATION", "true").lower() == "true"
ENABLE_SYNC_LOG = os.getenv("ENABLE_SYNC_LOG", "true").lower() == "true"

SF_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}
STAGE_NAME = os.getenv("SNOWFLAKE_STAGE", "AGRI_DRIVE_STAGE")


def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def list_files(service):
    """List all files in the target Google Drive folder."""
    query = f"'{FOLDER_ID}' in parents and trashed = false"
    files = []
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size, mimeType)",
            pageSize=100,
            pageToken=page_token
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def is_allowed(filename: str) -> bool:
    if not ALLOWED_EXTENSIONS or ALLOWED_EXTENSIONS == [""]:
        return True
    return any(filename.lower().endswith(ext.strip()) for ext in ALLOWED_EXTENSIONS)


def download_file(service, file_id: str, filename: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = DOWNLOAD_DIR / filename
    request = service.files().get_media(fileId=file_id)
    with open(dest, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_synced_hashes(sf_conn) -> set:
    """Get already-synced file hashes to avoid duplicates."""
    if not ENABLE_DUPLICATE_CHECK:
        return set()
    cur = sf_conn.cursor()
    cur.execute("SELECT SHA256_HASH FROM AGRIPULSE.RAW.DRIVE_SYNC_LOG WHERE STATUS = 'SUCCESS'")
    return {row[0] for row in cur.fetchall()}


def upload_to_stage(sf_conn, local_path: Path):
    stage_path = f"@{SF_CONFIG['database']}.{SF_CONFIG['schema']}.{STAGE_NAME}/{STAGE_SUBDIR}"
    cur = sf_conn.cursor()
    cur.execute(f"PUT 'file://{local_path.resolve()}' '{stage_path}' AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    log.info(f"Uploaded {local_path.name} → {stage_path}")


def log_sync(sf_conn, file_id, filename, size, mime_type, sha256, stage_path, status="SUCCESS"):
    if not ENABLE_SYNC_LOG:
        return
    cur = sf_conn.cursor()
    cur.execute(
        """INSERT INTO AGRIPULSE.RAW.DRIVE_SYNC_LOG 
           (FILE_ID, FILE_NAME, FILE_SIZE, MIME_TYPE, SHA256_HASH, STAGE_PATH, STATUS)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (file_id, filename, size, mime_type, sha256, stage_path, status)
    )


def run():
    log.info("Starting Google Drive → Snowflake sync")
    log.info(f"Target folder: {FOLDER_ID}")

    drive = get_drive_service()
    files = list_files(drive)
    log.info(f"Found {len(files)} file(s) in Drive folder")

    sf_conn = snowflake.connector.connect(**SF_CONFIG)
    synced_hashes = get_synced_hashes(sf_conn)

    synced, skipped, failed = 0, 0, 0
    for f in files:
        name = f["name"]
        file_id = f["id"]
        size = int(f.get("size", 0))
        mime = f.get("mimeType", "")

        if not is_allowed(name):
            log.debug(f"Skipped (extension filter): {name}")
            skipped += 1
            continue
        if size > MAX_FILE_SIZE:
            log.warning(f"Skipped (too large: {size / 1024 / 1024:.1f}MB): {name}")
            skipped += 1
            continue

        try:
            local_path = download_file(drive, file_id, name)
            file_hash = sha256_file(local_path) if ENABLE_SHA256 else ""

            if file_hash in synced_hashes:
                log.info(f"Skipped (duplicate): {name}")
                skipped += 1
                if AUTO_DELETE:
                    local_path.unlink()
                continue

            upload_to_stage(sf_conn, local_path)
            stage_path = f"@{STAGE_NAME}/{STAGE_SUBDIR}/{name}"
            log_sync(sf_conn, file_id, name, size, mime, file_hash, stage_path)
            synced += 1

            if AUTO_DELETE:
                local_path.unlink()

        except Exception as e:
            log.error(f"Failed to sync {name}: {e}")
            log_sync(sf_conn, file_id, name, size, mime, "", "", "FAILED")
            failed += 1

    sf_conn.close()
    log.info(f"Sync complete: {synced} uploaded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    run()
