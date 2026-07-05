from typing import Tuple

_MIME_BY_EXTENSION = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def load_image_bytes(uploaded_file, extension: str) -> Tuple[bytes, str]:
    """
    Reads the raw bytes and resolves the mime type for an uploaded image.
    Actual mindmap generation (including handwriting recognition) happens in
    ai.fallback_chain.AIFallbackChain.generate_markdown_from_image, since that
    is where the vision-capable model / OCR fallback lives.
    """
    image_bytes = uploaded_file.read()
    mime_type = _MIME_BY_EXTENSION.get(extension.lower(), "image/png")
    return image_bytes, mime_type
