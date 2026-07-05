import io
import traceback
from typing import List

import google.generativeai as genai
from PIL import Image

import config
from ai.base_provider import (
    BaseAIProvider,
    IMAGE_MINDMAP_PROMPT,
    MINDMAP_PROMPT_TEMPLATE,
    MULTI_PAGE_IMAGE_MINDMAP_PROMPT,
)
from ai.exceptions import ProviderError, QuotaExceededError


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        k in msg
        for k in (
            "quota",
            "rate limit",
            "429",
            "resource_exhausted",
            "resource exhausted",
        )
    )


class GeminiProvider(BaseAIProvider):
    name = "Gemini"
    supports_vision = True

    def is_configured(self) -> bool:
        return config.is_gemini_configured()

    def _configure(self):
        genai.configure(api_key=config.get_gemini_key())

    def generate_markdown(self, text: str) -> str:
        self._require_configured()
        self._configure()

        try:
            model = genai.GenerativeModel(config.GEMINI_TEXT_MODEL)

            sample = text[: config.MAX_CHARS_FOR_AI]

            prompt = MINDMAP_PROMPT_TEMPLATE.format(text=sample)

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": config.AI_MAX_OUTPUT_TOKENS,
                },
            )

            if not response or not response.text or not response.text.strip():
                raise ProviderError("Gemini returned an empty response")

            return response.text.strip()

        except (QuotaExceededError, ProviderError):
            raise

        except Exception as exc:
            traceback.print_exc()

            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc

            raise ProviderError(
                f"Gemini text generation failed:\n{repr(exc)}"
            ) from exc

    def generate_markdown_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        self._require_configured()
        self._configure()

        try:
            image = Image.open(io.BytesIO(image_bytes))

            model = genai.GenerativeModel(config.GEMINI_VISION_MODEL)

            response = model.generate_content(
                [IMAGE_MINDMAP_PROMPT, image],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": config.AI_MAX_OUTPUT_TOKENS,
                },
            )

            if not response or not response.text or not response.text.strip():
                raise ProviderError("Gemini Vision returned an empty response")

            return response.text.strip()

        except (QuotaExceededError, ProviderError):
            raise

        except Exception as exc:
            traceback.print_exc()

            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc

            raise ProviderError(
                f"Gemini vision generation failed:\n{repr(exc)}"
            ) from exc

    def generate_markdown_from_images(self, images_bytes: List[bytes]) -> str:
        self._require_configured()
        self._configure()

        try:
            pil_images = [Image.open(io.BytesIO(b)) for b in images_bytes]

            model = genai.GenerativeModel(config.GEMINI_VISION_MODEL)

            content = [MULTI_PAGE_IMAGE_MINDMAP_PROMPT, *pil_images]

            response = model.generate_content(
                content,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": config.AI_MAX_OUTPUT_TOKENS,
                },
            )

            if not response or not response.text or not response.text.strip():
                raise ProviderError("Gemini Vision returned an empty response")

            return response.text.strip()

        except (QuotaExceededError, ProviderError):
            raise

        except Exception as exc:
            traceback.print_exc()

            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc

            raise ProviderError(
                f"Gemini multi-image vision generation failed:\n{repr(exc)}"
            ) from exc