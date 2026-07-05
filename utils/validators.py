from typing import Optional, Tuple

import config


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_upload(uploaded_file) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Returns (is_valid, category, error_message).
    category is one of: "document", "image", or None if invalid.
    """
    extension = get_extension(uploaded_file.name)

    if extension not in config.SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(config.SUPPORTED_EXTENSIONS))
        return False, None, f"Unsupported file type '.{extension}'. Supported: {supported}"

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_MB:
        return False, None, f"File is {size_mb:.1f} MB, which exceeds the {config.MAX_UPLOAD_MB} MB limit"

    return True, config.SUPPORTED_EXTENSIONS[extension], None
