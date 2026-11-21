
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    TABLE_UPLOAD_DIR,
    DOCUMENT_UPLOAD_DIR
)

from backend.database.db import get_connection


# ------------------------------------------------
# 1. Upload one file
# ------------------------------------------------

def upload_file(file):

    original_name = Path(
        file.filename or ""
    ).name

    extension = Path(
        original_name
    ).suffix.lower()

    # Validate extension
    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "Unsupported file format"
        )

    # Select destination folder
    if extension == ".csv":

        destination = TABLE_UPLOAD_DIR

    else:

        destination = DOCUMENT_UPLOAD_DIR

    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    # Generate unique file ID
    file_id = str(
        uuid.uuid4()
    )

    stored_name = (
        f"{file_id}{extension}"
    )

    file_path = destination / stored_name

    total_size = 0

    connection = None

    try:

        # Save uploaded file
        with open(
            file_path,
            "wb"
        ) as output:

            while True:

                chunk = file.file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:

                    raise ValueError(
                        "File exceeds the 20 MB limit"
                    )

                output.write(chunk)

        if total_size == 0:

            raise ValueError(
                "Empty files are not allowed"
            )

        uploaded_at = datetime.now(
            timezone.utc
        ).isoformat()

        # Save metadata in SQLite
        connection = get_connection()

        connection.execute(
            """
            INSERT INTO uploaded_files
            (
                file_id,
                filename,
                stored_path,
                file_type,
                file_size,
                uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                original_name,
                str(file_path),
                extension,
                total_size,
                uploaded_at
            )
        )

        connection.commit()

        return {
            "file_id": file_id,
            "filename": original_name,
            "file_type": extension,
            "file_size": total_size,
            "stored_path": str(file_path),
            "message": "File uploaded successfully"
        }

    except Exception:

        if connection is not None:
            connection.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    finally:

        if connection is not None:
            connection.close()


# ------------------------------------------------
# 2. Get uploaded files
# ------------------------------------------------

def get_uploaded_files():

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                file_id,
                filename,
                file_type,
                file_size,
                uploaded_at
            FROM uploaded_files
            ORDER BY uploaded_at DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()
