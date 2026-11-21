
import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from backend.config import BASE_DIR


# Folder containing the original company documents
DOCUMENT_DIR = BASE_DIR / "data" / "documents"


# ------------------------------------------------
# 1. Identify document family
# ------------------------------------------------

def identify_document_family(filename):

    name = filename.lower()

    if "return_policy" in name or "return_policy" in name.replace("-", "_"):
        return "Return & Refund Policy"

    elif "jd_ml_engineer" in name:
        return "Machine Learning Engineer JD"

    elif "warranty_terms" in name:
        return "VoltCare Warranty Terms"

    elif "store_operations" in name:
        return "Store Operations Notice"

    return "Unknown Document"


# ------------------------------------------------
# 2. Extract document date from filename
# ------------------------------------------------

def extract_document_date(filename):

    match = re.search(
        r"(\d{4}-\d{2}-\d{2})",
        filename
    )

    if match:
        return match.group(1)

    return None


# ------------------------------------------------
# 3. Extract text from PDF
# ------------------------------------------------

def extract_pdf(file_path):

    reader = PdfReader(str(file_path))

    extracted_pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        extracted_pages.append({
            "text": text,
            "page": page_number
        })

    return extracted_pages


# ------------------------------------------------
# 4. Extract text from DOCX
# ------------------------------------------------

def extract_docx(file_path):

    document = Document(str(file_path))

    extracted_paragraphs = []

    # Extract paragraphs
    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:

            extracted_paragraphs.append({
                "text": text,
                "page": None
            })

    # Extract tables
    for table in document.tables:

        for row in table.rows:

            row_text = " | ".join(
                cell.text.strip()
                for cell in row.cells
            )

            if row_text.strip():

                extracted_paragraphs.append({
                    "text": row_text,
                    "page": None
                })

    return extracted_paragraphs


# ------------------------------------------------
# 5. Extract text from TXT
# ------------------------------------------------

def extract_txt(file_path):

    text = file_path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    return [{
        "text": text,
        "page": None
    }]


# ------------------------------------------------
# 6. Read one document
# ------------------------------------------------

def read_document(
    file_path,
    original_filename=None,
    source_id=None
):

    file_path = Path(file_path)

    extension = file_path.suffix.lower()

    if extension == ".pdf":

        content = extract_pdf(file_path)

    elif extension == ".docx":

        content = extract_docx(file_path)

    elif extension == ".txt":

        content = extract_txt(file_path)

    else:

        raise ValueError(
            f"Unsupported document format: {extension}"
        )

    # Use original filename for metadata and citations.
    # Stored file may have a UUID filename.
    display_filename = (
        original_filename
        or file_path.name
    )

    return {
        "filename": display_filename,

        "source_id": (
            source_id
            or display_filename
        ),

        "document_family": identify_document_family(
            display_filename
        ),

        "document_date": extract_document_date(
            display_filename
        ),

        "file_type": extension,

        "content": content
    }


# ------------------------------------------------
# 7. Load all original documents
# ------------------------------------------------

def load_all_documents():

    documents = []

    if not DOCUMENT_DIR.exists():

        raise FileNotFoundError(
            f"Document folder not found: {DOCUMENT_DIR}"
        )

    for file_path in DOCUMENT_DIR.iterdir():

        if not file_path.is_file():
            continue

        if file_path.name.startswith("._"):
            continue

        if file_path.suffix.lower() not in [
            ".pdf",
            ".docx",
            ".txt"
        ]:
            continue

        document = read_document(file_path)

        documents.append(document)

        print(
            f"Loaded: {document['filename']} "
            f"| Family: {document['document_family']} "
            f"| Date: {document['document_date']}"
        )

    return documents


# ------------------------------------------------
# 8. Print document summary
# ------------------------------------------------

def get_document_summary(documents):

    print("\nDOCUMENT SUMMARY")
    print("----------------")

    for document in documents:

        total_sections = len(
            document["content"]
        )

        print(
            f"{document['filename']} "
            f"-> {total_sections} content sections"
        )
