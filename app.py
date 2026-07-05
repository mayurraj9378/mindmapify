import streamlit as st
import streamlit.components.v1 as components

import config
from ai.fallback_chain import AIFallbackChain
from ai.gemini_provider import GeminiProvider
from ai.groq_provider import GroqProvider
from ai.hf_ocr import HFHandwritingOCR
from extractors.docx_extractor import extract_text_from_docx
from extractors.image_extractor import load_image_bytes
from extractors.pdf_extractor import extract_text_from_pdf, render_pdf_pages_to_images
from mindmap.html_renderer import create_markmap_html
from utils.validators import get_extension, validate_upload

st.set_page_config(page_title="Mindmapify - AI-Powered Mindmaps", layout="wide")


@st.cache_resource
def get_ai_chain() -> AIFallbackChain:
    """Built once per server process. Order = Gemini -> Groq -> offline rule-based."""
    providers = [GeminiProvider(), GroqProvider()]
    return AIFallbackChain(providers=providers, hf_ocr=HFHandwritingOCR())


def init_session_state():
    for key in (
        "markdown_content",
        "html_content",
        "generated_by",
        "extracted_text",
        "file_processed",
        "attempts",
        "effective_category",
        "scanned_pages",
    ):
        if key not in st.session_state:
            st.session_state[key] = None


def render_sidebar():
    with st.sidebar:
        st.title("📌 Mindmapify")
        st.write("Convert PDFs, Word docs, and images (including handwriting) into interactive mindmaps.")
        st.markdown("---")

        st.markdown("### 🤖 AI Providers")
        st.write("✅ Gemini" if config.is_gemini_configured() else "⬜ Gemini (not configured)")
        st.write("✅ Groq" if config.is_groq_configured() else "⬜ Groq (not configured)")
        st.write("✅ HF Handwriting OCR" if config.is_hf_configured() else "⬜ HF Handwriting OCR (not configured)")
        st.caption("Keys are read from your .env file and are never displayed here.")

        if not (config.is_gemini_configured() or config.is_groq_configured()):
            st.warning("No AI provider configured - the offline rule-based generator will be used.")

        st.markdown("---")
        st.markdown("### 📖 How to use")
        st.markdown(
            "1. Upload a PDF, Word doc, or image\n"
            "2. Wait for text extraction\n"
            "3. Click Generate Mindmap\n"
            "4. Drag to pan, use controls to zoom\n"
            "5. Download as Markdown or HTML"
        )

        st.markdown("---")
        if st.button("🔄 Clear All", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def handle_document(uploaded_file, extension: str):
    if st.session_state.get("file_processed"):
        return

    with st.spinner("📖 Extracting text..."):
        if extension == "pdf":
            progress_bar = st.progress(0)
            status = st.empty()

            def on_progress(current, total):
                progress_bar.progress(current / total)
                status.text(f"Processing page {current}/{total}")

            text = extract_text_from_pdf(uploaded_file, progress_callback=on_progress)
            progress_bar.empty()
            status.empty()
        elif extension == "docx":
            text = extract_text_from_docx(uploaded_file)
        else:
            text = None

    if text:
        st.session_state["extracted_text"] = text
        st.session_state["effective_category"] = "document"
        st.session_state["file_processed"] = True
        return

    if extension == "pdf":
        # No embedded text layer - this is almost always a scanned/photographed
        # PDF (e.g. photos of handwritten notes exported page-by-page). Fall
        # back to rendering each page as an image and reading it with the
        # vision-capable AI chain, same as a direct image upload.
        st.info(
            "📸 No embedded text layer found - this looks like a scanned/photographed PDF. "
            "Falling back to image-based AI reading (this can take a bit longer)."
        )
        with st.spinner("🖼️ Rendering pages as images..."):
            page_images = render_pdf_pages_to_images(uploaded_file)

        if not page_images:
            st.warning("⚠ Could not render any pages from this PDF.")
            return

        st.session_state["scanned_pages"] = page_images
        st.session_state["effective_category"] = "scanned_pdf"
        st.session_state["file_processed"] = True
        return

    st.warning("⚠ No readable text found in this file.")


def handle_image(uploaded_file, extension: str):
    if st.session_state.get("file_processed"):
        return
    image_bytes, mime_type = load_image_bytes(uploaded_file, extension)
    st.session_state["image_bytes"] = image_bytes
    st.session_state["image_mime"] = mime_type
    st.session_state["file_processed"] = True
    st.image(image_bytes, caption="Uploaded image", use_container_width=True)


def render_generate_controls(category: str):
    col1, col2 = st.columns(2)

    with col1:
        generate_btn = st.button(
            "⚡ Generate Mindmap",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.get("markdown_content") is not None,
        )
        if generate_btn:
            chain = get_ai_chain()
            with st.spinner("🤖 Generating mindmap... this may take a moment."):
                if category == "image":
                    result = chain.generate_markdown_from_image(
                        st.session_state["image_bytes"], st.session_state["image_mime"]
                    )
                elif category == "scanned_pdf":
                    result = chain.generate_markdown_from_images(st.session_state["scanned_pages"])
                else:
                    result = chain.generate_markdown(st.session_state["extracted_text"])

            st.session_state["markdown_content"] = result.markdown
            st.session_state["html_content"] = create_markmap_html(result.markdown)
            st.session_state["generated_by"] = result.generated_by
            st.session_state["attempts"] = result.attempts
            st.rerun()

    with col2:
        if st.button("🧹 Clear Mindmap", use_container_width=True):
            st.session_state["markdown_content"] = None
            st.session_state["html_content"] = None
            st.session_state["generated_by"] = None
            st.session_state["attempts"] = None
            st.rerun()


def render_mindmap():
    if not st.session_state.get("markdown_content"):
        return

    st.markdown("---")
    st.caption(f"Generated by: **{st.session_state['generated_by']}**")

    attempts = st.session_state.get("attempts") or []
    if attempts:
        icon = {"success": "✅", "quota_exceeded": "⏳", "error": "❌", "skipped": "⬜"}
        with st.expander("🔍 Generation details (what was tried and why)"):
            for attempt in attempts:
                line = f"{icon.get(attempt.status, '•')} **{attempt.provider}** — {attempt.status}"
                if attempt.detail:
                    line += f": {attempt.detail}"
                st.markdown(line)

    tab1, tab2 = st.tabs(["📊 Interactive Mindmap", "📝 Markdown Source"])

    with tab1:
        st.markdown("🖱️ **Drag** to pan • 🎯 **Click** nodes to expand/collapse • 🔍 **Controls** to zoom")
        st.download_button(
            "📥 Export Mindmap (HTML)",
            data=st.session_state["html_content"],
            file_name="mindmap.html",
            mime="text/html",
        )
        components.html(st.session_state["html_content"], height=700, scrolling=False)

    with tab2:
        st.code(st.session_state["markdown_content"], language="markdown")
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "📄 Download as Markdown",
                data=st.session_state["markdown_content"],
                file_name="mindmap.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_b:
            st.download_button(
                "🌐 Download as HTML",
                data=st.session_state["html_content"],
                file_name="mindmap.html",
                mime="text/html",
                use_container_width=True,
            )


def main():
    init_session_state()
    render_sidebar()

    st.title("📚 Mindmapify - Document & Image to AI Mindmap Generator")
    st.markdown("Transform PDFs, Word docs, and images (including handwritten notes) into interactive mindmaps.")

    uploaded_file = st.file_uploader(
        "📂 Upload a PDF, Word document, or image",
        type=list(config.SUPPORTED_EXTENSIONS.keys()),
    )

    if not uploaded_file:
        st.info("👆 Upload a file to get started")
        return

    is_valid, category, error = validate_upload(uploaded_file)
    if not is_valid:
        st.error(error)
        return

    extension = get_extension(uploaded_file.name)

    if category == "document":
        handle_document(uploaded_file, extension)
        effective_category = st.session_state.get("effective_category")

        if effective_category == "document":
            text = st.session_state.get("extracted_text")
            if text:
                st.success(f"✅ Extracted {len(text):,} characters")
                with st.expander("📄 Preview extracted text"):
                    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
                render_generate_controls(effective_category)
        elif effective_category == "scanned_pdf":
            pages = st.session_state.get("scanned_pages") or []
            if pages:
                st.success(f"✅ Rendered {len(pages)} page(s) as images for AI reading")
                render_generate_controls(effective_category)
    else:  # image
        handle_image(uploaded_file, extension)
        st.success("✅ Image loaded - Gemini Vision will read typed and handwritten text directly")
        render_generate_controls(category)

    render_mindmap()


if __name__ == "__main__":
    main()
