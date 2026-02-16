"""
Layout Composer
Combines paper background, handwritten text, and diagrams into final page images.
"""

from typing import List, Dict
from PIL import Image


class LayoutComposer:
    """Composes final pages by layering paper, text, and diagrams."""

    def compose_page(
        self,
        paper: Image.Image,
        text_layer: Image.Image,
        diagrams: List[Dict],
        scale: float = 1.0,
    ) -> Image.Image:
        """
        Compose a single page from layers.

        Args:
            paper: Paper background (RGB)
            text_layer: Handwritten text (RGBA, transparent bg)
            diagrams: List of converted diagrams with positions
            scale: Coordinate scale factor

        Returns:
            Final composed page (RGB)
        """
        # Start with paper background
        page = paper.convert("RGBA")

        # Layer 1: Handwritten text
        if text_layer:
            # Resize text layer to match paper if needed
            if text_layer.size != page.size:
                text_layer = text_layer.resize(page.size, Image.Resampling.LANCZOS)

            page = Image.alpha_composite(page, text_layer)

        # Layer 2: Hand-drawn diagrams
        for diagram in diagrams:
            converted = diagram.get("converted_image")
            if converted is None:
                continue

            if isinstance(converted, bytes):
                import io
                converted = Image.open(io.BytesIO(converted)).convert("RGBA")
            elif not isinstance(converted, Image.Image):
                continue

            # Get position
            x = int(diagram.get("x", 0) * scale)
            y = int(diagram.get("y", 0) * scale)
            w = int(diagram.get("width", converted.width) * scale)
            h = int(diagram.get("height", converted.height) * scale)

            # Resize diagram to fit its region
            converted = converted.resize((w, h), Image.Resampling.LANCZOS)

            # Ensure it's RGBA for compositing
            if converted.mode != "RGBA":
                converted = converted.convert("RGBA")

            # Paste with transparency
            page.paste(converted, (x, y), converted)

        return page.convert("RGB")

    def compose_document(
        self,
        pages_data: List[Dict],
        scale: float = 1.0,
    ) -> List[Image.Image]:
        """
        Compose all pages of a document.

        Args:
            pages_data: List of page data dicts, each containing:
                - paper: paper background Image
                - text_layer: handwritten text Image
                - diagrams: list of diagram dicts

        Returns:
            List of composed page Images
        """
        composed = []

        for page_data in pages_data:
            page = self.compose_page(
                paper=page_data["paper"],
                text_layer=page_data["text_layer"],
                diagrams=page_data.get("diagrams", []),
                scale=scale,
            )
            composed.append(page)

        return composed
