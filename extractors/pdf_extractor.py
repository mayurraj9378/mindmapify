from typing import Callable, List, Optional

from PyPDF2 import PdfReader


def extract_text_from_pdf(
    pdf_file,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Optional[str]:
    """
    Extract all text from a PDF file-like object.

    progress_callback(current_page, total_pages) is called after each page,
    letting the UI layer (Streamlit) render its own progress bar without this
    module knowing anything about Streamlit.

    Returns None if the PDF has no extractable text layer at all (e.g. it's
    scanned pages or photos of handwritten notes glued into a PDF) - use
    render_pdf_pages_to_images() as a fallback in that case.
    """
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)
    text_parts = []

    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
        if progress_callback:
            progress_callback(idx + 1, total_pages)

    text = "\n".join(text_parts).strip()
    return text or None


def render_pdf_pages_to_images(pdf_file, dpi: int = 150, max_pages: int = 20) -> List[bytes]:
    """
    Rasterizes each page of a PDF to PNG bytes. Used when a PDF has no
    extractable text layer - i.e. it's scanned/photographed pages (like
    handwritten notes exported to PDF) rather than real digital text.
    Each page can then be sent through the same vision-capable AI chain
    used for direct image uploads.
    """
    import fitz  # PyMuPDF, imported lazily since it's only needed for this path

    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    images = []
    for page in doc[:max_pages]:
        pix = page.get_pixmap(matrix=matrix)
        images.append(pix.tobytes("png"))
    doc.close()
    return images
