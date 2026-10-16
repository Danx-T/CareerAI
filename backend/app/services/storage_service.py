import os
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings


async def save_upload_file(file: UploadFile, user_id: int) -> str:
    """Save an uploaded file and return the file path."""
    user_dir = Path(settings.UPLOAD_DIR) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = "".join(
        c for c in file.filename if c.isalnum() or c in "._- "
    ).strip()
    file_path = user_dir / safe_name

    # Handle duplicates
    counter = 1
    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix
    while file_path.exists():
        file_path = user_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(chunk)

    return str(file_path)


def delete_file(file_path: str) -> None:
    """Delete a file from storage."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not delete file {file_path}: {e}")


def get_file_size_mb(file_path: str) -> float:
    """Return file size in MB."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return 0.0
