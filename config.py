"""
Central configuration for Mindmapify.

Loads all secrets from .env ONLY. Nothing here is ever printed, logged,
or returned to the Streamlit UI. If you need to check "is a key present",
use the boolean helpers below (is_gemini_configured(), etc.) - never
read GOOGLE_API_KEY / GROQ_API_KEY / HF_API_TOKEN directly in app.py.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Secrets (private module-level, not exported by name on purpose) ---- #
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
_HF_API_TOKEN = os.getenv("HF_API_TOKEN", "").strip()

# ---- Non-secret settings ---- #
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-flash-latest")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-flash-latest")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
HF_HANDWRITING_MODEL = os.getenv("HF_HANDWRITING_MODEL", "microsoft/trocr-large-handwritten")

MAX_CHARS_FOR_AI = int(os.getenv("MAX_CHARS_FOR_AI", "60000"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "8192"))


def is_gemini_configured() -> bool:
    return bool(_GOOGLE_API_KEY)


def is_groq_configured() -> bool:
    return bool(_GROQ_API_KEY)


def is_hf_configured() -> bool:
    return bool(_HF_API_TOKEN)


def get_gemini_key() -> str:
    """Only ever called server-side by the Gemini provider itself."""
    return _GOOGLE_API_KEY


def get_groq_key() -> str:
    return _GROQ_API_KEY


def get_hf_token() -> str:
    return _HF_API_TOKEN


SUPPORTED_EXTENSIONS = {
    "pdf": "document",
    "docx": "document",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
}
