import requests

import config
from ai.exceptions import ProviderError, QuotaExceededError

_HF_API_URL_TEMPLATE = "https://router.huggingface.co/hf-inference/models/{model}"


class HFHandwritingOCR:
    """
    Fallback handwriting recognizer using Hugging Face's free Inference API
    (default model: microsoft/trocr-large-handwritten).

    This only extracts raw text from the image - the extracted text is then
    handed to the normal text-based AI chain (Gemini/Groq) to be turned into
    a structured markdown mindmap.

    Note: TrOCR-style models work best on single lines/blocks of handwriting,
    not full multi-paragraph pages - treat this as a best-effort fallback.
    """

    name = "HF TrOCR (handwriting)"

    def is_configured(self) -> bool:
        return config.is_hf_configured()

    def extract_text(self, image_bytes: bytes) -> str:
        if not self.is_configured():
            raise ProviderError("Hugging Face API token not configured")

        url = _HF_API_URL_TEMPLATE.format(model=config.HF_HANDWRITING_MODEL)
        headers = {"Authorization": f"Bearer {config.get_hf_token()}"}

        try:
            response = requests.post(url, headers=headers, data=image_bytes, timeout=60)
        except requests.RequestException as exc:
            raise ProviderError(f"HF OCR request failed: {exc}") from exc

        if response.status_code == 429:
            raise QuotaExceededError("Hugging Face Inference API rate limit reached")
        if response.status_code == 410:
            raise ProviderError(
                "Hugging Face has retired this endpoint/model path - check for a newer router URL"
            )
        if response.status_code == 503:
            # Model is cold-loading on HF's shared infra - treat as a soft failure
            raise ProviderError("HF model is loading, please retry shortly")
        if not response.ok:
            raise ProviderError(f"HF OCR request failed: {response.status_code} {response.text[:200]}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("HF OCR returned a non-JSON response") from exc

        if isinstance(data, list) and data and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        if isinstance(data, dict) and "error" in data:
            raise ProviderError(f"HF OCR error: {data['error']}")

        raise ProviderError("HF OCR returned an unexpected response shape")
