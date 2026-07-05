from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ai.base_provider import BaseAIProvider
from ai.exceptions import NotConfiguredError, ProviderError, QuotaExceededError
from ai.hf_ocr import HFHandwritingOCR
from mindmap.simple_fallback import generate_simple_mindmap

OFFLINE_FALLBACK_NAME = "Rule-based (offline fallback)"


@dataclass
class Attempt:
    """One step of the fallback chain, kept so the UI can show exactly what happened."""
    provider: str
    status: str  # "skipped", "quota_exceeded", "error", "success"
    detail: str = ""


@dataclass
class GenerationResult:
    markdown: str
    generated_by: str
    attempts: List[Attempt] = field(default_factory=list)


class AIFallbackChain:
    """
    Tries text providers in the given order (e.g. Gemini -> Groq).
    If every configured provider fails or is missing a key, falls back to a
    free, offline, rule-based markdown generator so the app never hard-fails.

    Every step (skipped/quota/error/success) is recorded in `attempts` so
    failures are visible in the UI instead of silently swallowed.
    """

    def __init__(self, providers: List[BaseAIProvider], hf_ocr: Optional[HFHandwritingOCR] = None):
        self.providers = providers
        self.hf_ocr = hf_ocr or HFHandwritingOCR()

    def generate_markdown(self, text: str) -> GenerationResult:
        attempts: List[Attempt] = []
        for provider in self.providers:
            if not provider.is_configured():
                attempts.append(Attempt(provider.name, "skipped", "no API key configured"))
                continue
            try:
                markdown = provider.generate_markdown(text)
                if markdown and markdown.strip():
                    attempts.append(Attempt(provider.name, "success"))
                    return GenerationResult(markdown, provider.name, attempts)
                attempts.append(Attempt(provider.name, "error", "empty response"))
            except QuotaExceededError as exc:
                attempts.append(Attempt(provider.name, "quota_exceeded", str(exc)))
            except NotConfiguredError as exc:
                attempts.append(Attempt(provider.name, "skipped", str(exc)))
            except ProviderError as exc:
                attempts.append(Attempt(provider.name, "error", str(exc)))

        attempts.append(Attempt(OFFLINE_FALLBACK_NAME, "success", "used as last resort"))
        return GenerationResult(generate_simple_mindmap(text), OFFLINE_FALLBACK_NAME, attempts)

    def generate_markdown_from_image(self, image_bytes: bytes, mime_type: str) -> GenerationResult:
        """
        1. Try vision-capable providers directly (e.g. Gemini Vision) - handles
           handwriting natively in one call.
        2. If those fail/hit quota, OCR the image via Hugging Face TrOCR, then
           run the extracted text through the normal text chain.
        3. If everything fails, offline rule-based fallback.
        """
        attempts: List[Attempt] = []
        vision_providers = [p for p in self.providers if p.supports_vision]

        for provider in vision_providers:
            if not provider.is_configured():
                attempts.append(Attempt(f"{provider.name} Vision", "skipped", "no API key configured"))
                continue
            try:
                markdown = provider.generate_markdown_from_image(image_bytes, mime_type)
                if markdown and markdown.strip():
                    attempts.append(Attempt(f"{provider.name} Vision", "success"))
                    return GenerationResult(markdown, f"{provider.name} Vision", attempts)
                attempts.append(Attempt(f"{provider.name} Vision", "error", "empty response"))
            except QuotaExceededError as exc:
                attempts.append(Attempt(f"{provider.name} Vision", "quota_exceeded", str(exc)))
            except ProviderError as exc:
                attempts.append(Attempt(f"{provider.name} Vision", "error", str(exc)))

        if not self.hf_ocr.is_configured():
            attempts.append(Attempt(self.hf_ocr.name, "skipped", "no API token configured"))
        else:
            try:
                extracted_text = self.hf_ocr.extract_text(image_bytes)
                if extracted_text and extracted_text.strip():
                    attempts.append(Attempt(self.hf_ocr.name, "success", f"extracted {len(extracted_text)} chars"))
                    text_result = self.generate_markdown(extracted_text)
                    attempts.extend(text_result.attempts)
                    return GenerationResult(
                        text_result.markdown,
                        f"{self.hf_ocr.name} -> {text_result.generated_by}",
                        attempts,
                    )
                attempts.append(Attempt(self.hf_ocr.name, "error", "OCR returned no text"))
            except QuotaExceededError as exc:
                attempts.append(Attempt(self.hf_ocr.name, "quota_exceeded", str(exc)))
            except ProviderError as exc:
                attempts.append(Attempt(self.hf_ocr.name, "error", str(exc)))

        attempts.append(Attempt(OFFLINE_FALLBACK_NAME, "success", "used as last resort - no provider could read the image"))
        return GenerationResult(
            generate_simple_mindmap("No readable text could be extracted from this image."),
            OFFLINE_FALLBACK_NAME,
            attempts,
        )

    def generate_markdown_from_images(self, images_bytes: List[bytes]) -> GenerationResult:
        """
        For scanned/photographed multi-page documents - e.g. a PDF made of
        photos of handwritten notebook pages with no real text layer.
        1. Try a vision-capable provider with all pages in one call (Gemini
           can read multiple images together and merge them into one mindmap).
        2. If that fails/hits quota, OCR each page individually via HF TrOCR,
           concatenate the text, then run it through the normal text chain.
        3. If everything fails, offline rule-based fallback.
        """
        attempts: List[Attempt] = []
        vision_providers = [p for p in self.providers if p.supports_vision]

        for provider in vision_providers:
            if not provider.is_configured():
                attempts.append(Attempt(f"{provider.name} Vision", "skipped", "no API key configured"))
                continue
            try:
                markdown = provider.generate_markdown_from_images(images_bytes)
                if markdown and markdown.strip():
                    attempts.append(Attempt(f"{provider.name} Vision", "success"))
                    return GenerationResult(
                        markdown, f"{provider.name} Vision ({len(images_bytes)} pages)", attempts
                    )
                attempts.append(Attempt(f"{provider.name} Vision", "error", "empty response"))
            except QuotaExceededError as exc:
                attempts.append(Attempt(f"{provider.name} Vision", "quota_exceeded", str(exc)))
            except ProviderError as exc:
                attempts.append(Attempt(f"{provider.name} Vision", "error", str(exc)))

        if not self.hf_ocr.is_configured():
            attempts.append(Attempt(self.hf_ocr.name, "skipped", "no API token configured"))
        else:
            page_texts = []
            failed_pages = 0
            for image_bytes in images_bytes:
                try:
                    page_text = self.hf_ocr.extract_text(image_bytes)
                    if page_text and page_text.strip():
                        page_texts.append(page_text.strip())
                except ProviderError:
                    failed_pages += 1
                    continue

            if page_texts:
                attempts.append(
                    Attempt(
                        self.hf_ocr.name,
                        "success",
                        f"extracted text from {len(page_texts)}/{len(images_bytes)} pages"
                        + (f" ({failed_pages} failed)" if failed_pages else ""),
                    )
                )
                text_result = self.generate_markdown("\n\n".join(page_texts))
                attempts.extend(text_result.attempts)
                return GenerationResult(
                    text_result.markdown, f"{self.hf_ocr.name} -> {text_result.generated_by}", attempts
                )
            attempts.append(Attempt(self.hf_ocr.name, "error", "OCR returned no text from any page"))

        attempts.append(
            Attempt(OFFLINE_FALLBACK_NAME, "success", "used as last resort - no provider could read the pages")
        )
        return GenerationResult(
            generate_simple_mindmap("No readable text could be extracted from these scanned pages."),
            OFFLINE_FALLBACK_NAME,
            attempts,
        )
