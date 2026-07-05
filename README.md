# Mindmapify

Turn PDFs, Word documents, and images (typed **or handwritten**) into interactive,
AI-structured mindmaps.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in whichever keys you have
streamlit run app.py
```

You don't need all three keys. The app degrades gracefully:
- No keys at all → still works, using the offline rule-based generator.
- Only `GOOGLE_API_KEY` → full text + vision support via Gemini.
- Add `GROQ_API_KEY` → automatic text fallback if Gemini's free quota runs out.
- Add `HF_API_TOKEN` → automatic handwriting-OCR fallback if Gemini Vision's quota runs out.

**No key is ever shown in the UI** - the sidebar only shows a ✅/⬜ status per provider.

## Architecture

```
app.py                 Streamlit UI only - no business logic
config.py              Loads .env, exposes is_configured() booleans (never raw keys)
extractors/
  pdf_extractor.py      PyPDF2-based text extraction, UI-agnostic progress callback
  docx_extractor.py     python-docx paragraph + table extraction
  image_extractor.py    Reads image bytes/mime type for the AI layer
ai/
  base_provider.py      Shared interface + prompt templates
  gemini_provider.py    Text + vision (handles handwriting directly)
  groq_provider.py      Text-only fallback
  hf_ocr.py             Handwriting-OCR fallback (Hugging Face TrOCR)
  fallback_chain.py     Tries providers in order, falls back to offline generator
mindmap/
  simple_fallback.py    Rule-based markdown generator (always works, no API needed)
  html_renderer.py      markmap.js HTML template (pan/zoom/export)
utils/
  validators.py         File type/size checks
```

## How the fallback chain works

**Documents (PDF/Word):**
1. Extract raw text locally (no API call).
2. Gemini structures it into markdown.
3. If Gemini's quota is hit → Groq takes over.
4. If both fail → offline rule-based generator (heading/bullet heuristics).

**Images (typed or handwritten):**
1. Gemini Vision reads the image directly and produces the markdown mindmap in one call.
2. If Gemini Vision's quota is hit → Hugging Face's TrOCR handwriting model extracts
   the raw text, which then goes through the same text chain (Gemini → Groq → offline).

## Adding a new provider

Implement `BaseAIProvider` in `ai/`, then add it to the list passed into
`AIFallbackChain` in `app.py`'s `get_ai_chain()`. Order in the list = priority order.

## Adding a new file type

Add an extractor function under `extractors/`, register the extension in
`config.SUPPORTED_EXTENSIONS`, and route it in `app.py`.
