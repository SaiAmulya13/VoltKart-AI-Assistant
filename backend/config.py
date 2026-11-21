
from pathlib import Path
import os
from dotenv import load_dotenv


# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables
load_dotenv(BASE_DIR / ".env")


# Main data folder
DATA_DIR = BASE_DIR / "data"


# Upload folders
UPLOAD_DIR = DATA_DIR / "uploads"

TABLE_UPLOAD_DIR = UPLOAD_DIR / "tables"

DOCUMENT_UPLOAD_DIR = UPLOAD_DIR / "documents"


# Database path
DATABASE_PATH = DATA_DIR / "voltkart.db"


# Allowed extensions
ALLOWED_EXTENSIONS = {
    ".csv",
    ".pdf",
    ".docx",
    ".txt"
}


# Maximum upload size: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024


# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# Validate configuration
def validate_config():

    if not GROQ_API_KEY:
        print("WARNING: Groq API key is missing.")

    TABLE_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DOCUMENT_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# Display configuration
def print_config():

    print("Project directory:", BASE_DIR)

    print("Database path:", DATABASE_PATH)

    print("Groq model:", GROQ_MODEL)

    print("Groq API key configured:", bool(GROQ_API_KEY))
