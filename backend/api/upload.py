
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.file_service import (
    upload_file,
    get_uploaded_files
)

from backend.services.document_service import (
    read_document
)

from backend.services.chunking_service import (
    split_document
)

from backend.services.embedding_service import (
    generate_embeddings
)

from backend.services.vector_store_service import (
    add_chunks_to_vector_store
)


router = APIRouter(
    prefix="/files",
    tags=["File Upload"]
)


# ------------------------------------------------
# 1. Upload file
# ------------------------------------------------

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...)
):

    try:

        # Step 1: Save file and metadata
        result = upload_file(file)

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail="File upload failed"
        )

    # ------------------------------------------------
    # 2. Process uploaded documents
    # ------------------------------------------------

    extension = result["file_type"]

    if extension in [
        ".pdf",
        ".docx",
        ".txt"
    ]:

        try:

            # Step 2: Read document text
            document = read_document(
                Path(result["stored_path"]),
                original_filename=result["filename"],
                source_id=result["file_id"]
            )

            # Step 3: Split document into chunks
            chunks = split_document(
                document
            )

            if not chunks:

                result["indexing_status"] = "no_text"

                result["indexed_chunks"] = 0

                result["message"] = (
                    "File uploaded, but no readable text "
                    "was found for indexing."
                )

            else:

                # Step 4: Generate embeddings
                embeddings = generate_embeddings(
                    chunks
                )

                # Step 5: Add chunks to existing FAISS index
                added_chunks = add_chunks_to_vector_store(
                    chunks,
                    embeddings
                )

                result["indexing_status"] = "completed"

                result["indexed_chunks"] = added_chunks

                result["message"] = (
                    "File uploaded and indexed successfully."
                )

        except Exception as error:

            # The file is already uploaded.
            # Keep it even if indexing fails.
            result["indexing_status"] = "failed"

            result["indexed_chunks"] = 0

            result["indexing_error"] = str(error)

            result["message"] = (
                "File uploaded successfully, "
                "but document indexing failed."
            )

    # ------------------------------------------------
    # 3. CSV upload status
    # ------------------------------------------------

    elif extension == ".csv":

        result["indexing_status"] = "not_applicable"

        result["message"] = (
            "CSV file uploaded successfully. "
            "CSV question-answering integration "
            "is handled separately."
        )

    # ------------------------------------------------
    # 4. Remove local path from API response
    # ------------------------------------------------

    result.pop(
        "stored_path",
        None
    )

    return {
        "success": True,
        "data": result
    }


# ------------------------------------------------
# 5. List uploaded files
# ------------------------------------------------

@router.get("/")
def list_files():

    return {
        "success": True,
        "files": get_uploaded_files()
    }
