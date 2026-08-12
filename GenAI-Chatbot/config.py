from pathlib import Path

import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DOCUMENTS
# ============================================================

DOCUMENTS_DIR = (
    BASE_DIR / "documents"
)


# ============================================================
# CHROMA
# ============================================================

CHROMA_DIR = (
    BASE_DIR / "data" / "chroma"
)


CHROMA_COLLECTION = (
    "banking_policies"
)


# ============================================================
# GEMINI
# ============================================================

GOOGLE_API_KEY = os.getenv(
    "GOOGLE_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

GEMINI_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001"
)


# ============================================================
# RAG
# ============================================================

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "1000"
    )
)

CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "150"
    )
)

RAG_TOP_K = int(
    os.getenv(
        "RAG_TOP_K",
        "5"
    )
)


# ============================================================
# FLASK
# ============================================================

FLASK_HOST = os.getenv(
    "FLASK_HOST",
    "127.0.0.1"
)

FLASK_PORT = int(
    os.getenv(
        "FLASK_PORT",
        "5000"
    )
)

FLASK_DEBUG = os.getenv(
    "FLASK_DEBUG",
    "true"
).lower() == "true"


FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-only-change-me"
)


# ============================================================
# VALIDATION
# ============================================================

def validate_config():

    if not GOOGLE_API_KEY:

        raise RuntimeError(
            "GOOGLE_API_KEY is missing "
            "from .env"
        )

    print()
    print("=" * 60)
    print("CONFIGURATION")
    print("=" * 60)

    print(
        "Documents:",
        DOCUMENTS_DIR
    )

    print(
        "Chroma:",
        CHROMA_DIR
    )

    print(
        "Gemini:",
        GEMINI_MODEL
    )

    print(
        "Embedding:",
        GEMINI_EMBEDDING_MODEL
    )

    print("=" * 60)
