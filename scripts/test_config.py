
from backend.config import (
    BASE_DIR,
    DATA_DIR,
    DATABASE_PATH,
    GROQ_API_KEY,
    GROQ_MODEL,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    validate_config,
    print_config
)

validate_config()

print_config()

print("\nAllowed Extensions:", ALLOWED_EXTENSIONS)

print("Maximum File Size:", MAX_FILE_SIZE)

print("Groq API Key Available:", bool(GROQ_API_KEY))
