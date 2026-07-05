from abc import ABC, abstractmethod
from typing import List

from ai.exceptions import NotConfiguredError


class BaseAIProvider(ABC):
    """Common interface so the fallback chain can treat every model the same way."""

    name: str = "base"
    supports_vision: bool = False

    @abstractmethod
    def is_configured(self) -> bool:
        """True if this provider has the API key/token it needs."""

    @abstractmethod
    def generate_markdown(self, text: str) -> str:
        """Turn raw extracted text into a hierarchical markdown mindmap."""

    def generate_markdown_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        """Only implemented by vision-capable providers (e.g. Gemini)."""
        raise NotImplementedError(f"{self.name} does not support direct image input")

    def generate_markdown_from_images(self, images_bytes: List[bytes]) -> str:
        """
        Multi-page variant: used for scanned/photographed multi-page PDFs
        (e.g. a notebook exported page-by-page with no real text layer).
        Only implemented by vision-capable providers.
        """
        raise NotImplementedError(f"{self.name} does not support multi-image input")

    def _require_configured(self):
        if not self.is_configured():
            raise NotConfiguredError(f"{self.name} has no API key configured")


MINDMAP_PROMPT_TEMPLATE = """
Create a comprehensive hierarchical markdown mindmap from the text below.
Use markdown headings (#, ##, ###, ####) for structure.
Focus on main topics, subtopics, and key concepts.
Include as much relevant detail as possible while maintaining a clear hierarchy.

Example format:
# Main Topic
## Subtopic 1
### Detail 1
- Key point 1
- Key point 2
#### Sub-detail
- Additional info
## Subtopic 2
### Detail 2
- Key point 3

Text to analyze:
{text}

Return ONLY the markdown mindmap, no extra commentary or explanations.
"""

IMAGE_MINDMAP_PROMPT = """
This image may contain typed or HANDWRITTEN text (notes, diagrams, sketches, etc).
Read everything you can, including handwriting, then produce a comprehensive
hierarchical markdown mindmap of its content using markdown headings (#, ##, ###, ####)
and bullet points for key details.

Return ONLY the markdown mindmap, no extra commentary or explanations.
"""

MULTI_PAGE_IMAGE_MINDMAP_PROMPT = """
These images are consecutive pages of the same document/notebook, in order.
They may contain typed or HANDWRITTEN text (notes, diagrams, sketches, etc).
Read everything you can across all pages, including handwriting, then produce
ONE comprehensive hierarchical markdown mindmap covering the whole document,
using markdown headings (#, ##, ###, ####) and bullet points for key details.
Merge related content across pages into the same branches where it makes sense,
rather than creating a separate top-level section per page.

Return ONLY the markdown mindmap, no extra commentary or explanations.
"""
