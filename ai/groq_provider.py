import config
from ai.base_provider import BaseAIProvider, MINDMAP_PROMPT_TEMPLATE
from ai.exceptions import ProviderError, QuotaExceededError


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("quota", "rate limit", "429", "rate_limit"))


class GroqProvider(BaseAIProvider):
    name = "Groq"
    supports_vision = False  # text-only fallback in this chain

    def is_configured(self) -> bool:
        return config.is_groq_configured()

    def generate_markdown(self, text: str) -> str:
        self._require_configured()
        try:
            from groq import Groq  # imported lazily so the package is optional

            client = Groq(api_key=config.get_groq_key())
            sample = text[: config.MAX_CHARS_FOR_AI]
            prompt = MINDMAP_PROMPT_TEMPLATE.format(text=sample)

            completion = client.chat.completions.create(
                model=config.GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=config.AI_MAX_OUTPUT_TOKENS,
            )
            content = completion.choices[0].message.content
            if not content or not content.strip():
                raise ProviderError("Groq returned an empty response")
            return content.strip()
        except (QuotaExceededError, ProviderError):
            raise
        except Exception as exc:
            if _is_quota_error(exc):
                raise QuotaExceededError(str(exc)) from exc
            raise ProviderError(f"Groq text generation failed: {exc}") from exc
