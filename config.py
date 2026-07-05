"""
Central configuration for Mindmapify.

Works in both:
1. Local development using .env
2. Streamlit Cloud using Secrets
"""

import os
from dotenv import load_dotenv

# Load local .env if available
load_dotenv()

# Try importing Streamlit (works on Streamlit Cloud)
try:
    import streamlit as st
except Exception:
    st = None


def get_setting(name: str, default: str = "") -> str:
    """
    Read settings in this order:
    1. Streamlit Secrets
    2. Environment Variables (.env)
    """

    # Streamlit Cloud Secrets
    if st is not None:
        try:
            if name in st.secrets:
                return str(st.secrets[name]).strip()
        except Exception:
            pass

    # Local .env
    return os.getenv(name, default).strip()


# ----------------------------
# Secrets
# ----------------------------

_GOOGLE_API_KEY = get_setting("GOOGLE_API_KEY")
_GROQ_API_KEY = get_setting("GROQ_API_KEY")
_HF_API_TOKEN = get_setting("HF_API_TOKEN")


# ----------------------------
# Models
# ----------------------------

GEMINI_TEXT_MODEL = get_setting(
    "GEMINI_TEXT_MODEL",
    "gemini-2.5-flash",
)

GEMINI_VISION_MODEL = get_setting(
    "GEMINI_VISION_MODEL",
    "gemini-2.5-flash",
)

GROQ_TEXT_MODEL = get_setting(
    "GROQ_TEXT_MODEL",
    "llama-3.3-70b-versatile",
)

HF_HANDWRITING_MODEL = get_setting(
    "HF_HANDWRITING_MODEL",
    "microsoft/trocr-large-handwritten",
)


# ----------------------------
# Limits
# ----------------------------

MAX_CHARS_FOR_AI = int(get_setting("MAX_CHARS_FOR_AI", "60000"))
MAX_UPLOAD_MB = int(get_setting("MAX_UPLOAD_MB", "25"))
AI_MAX_OUTPUT_TOKENS = int(get_setting("AI_MAX_OUTPUT_TOKENS", "8192"))


# ----------------------------
# Configuration Checks
# ----------------------------

def is_gemini_configured() -> bool:
    return bool(_GOOGLE_API_KEY)


def is_groq_configured() -> bool:
    return bool(_GROQ_API_KEY)


def is_hf_configured() -> bool:
    return bool(_HF_API_TOKEN)


# ----------------------------
# Secret Getters
# ----------------------------

def get_gemini_key() -> str:
    return _GOOGLE_API_KEY


def get_groq_key() -> str:
    return _GROQ_KEY


def get_hf_token() -> str:
    return _HF_API_TOKEN


# ----------------------------
# Supported Files
# ----------------------------

SUPPORTED_EXTENSIONS = {
    "pdf": "document",
    "docx": "document",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
}