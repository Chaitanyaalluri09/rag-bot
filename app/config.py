import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Create a .env file (see .env.example).")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
# Demo limits for visitor uploads
MAX_PDF_MB = 5
MAX_PAGES = 60
MAX_DOCS_PER_SESSION = 2
MAX_TOTAL_CHUNKS = 30000     # overall storage guard
SESSION_TTL_HOURS = 24       # visitor uploads are deleted after this
MAX_QUESTIONS_PER_SESSION = 20