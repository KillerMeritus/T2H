"""
Paper Renderer
Generates realistic paper backgrounds (lined, graph, blank, engineering).
"""

from typing import Dict
import random

from PIL import Image, ImageDraw, ImageFilter
import numpy as np


class PaperRenderer:
    """Renders realistic paper textures and backgrounds."""

    # Paper color palettes
    PAPER_COLORS = {
        "white": (253, 252, 250),
        "cream": (252, 247, 235),
        "yellow": (255, 253, 230),
        "aged": (245, 235, 220),
    }

    def render(
        self,
        paper_type: str,
        width: int,
        height: int,
        config: Dict = None,
    ) -> Image.Image:
        """
        Generate a paper background image.

        Args:
            paper_type: 'lined', 'graph', 'blank', 'engineering'
            width: Width in pixels
            height: Height in pixels
            config: Additional options

        Returns:
            PIL Image with paper background
        """
        config = config or {}
        paper_color_name = config.get("paper_color", "white")

        # Base paper
        base_color = self.PAPER_COLORS.get(paper_color_name, self.PAPER_COLORS["white"])
        paper = Image.new("RGB", (width, height), base_color)

        # Add subtle texture
        paper = self._add_grain(paper)

        # Add lines or grid
        draw = ImageDraw.Draw(paper)

        if paper_type == "lined":
            self._draw_lined(draw, width, height, config)
        elif paper_type == "graph":
            self._draw_graph(draw, width, height, config)
        elif paper_type == "engineering":
            self._draw_engineering(draw, width, height, config)
        # blank = no lines

        # Optional effects
        if config.get("enable_coffee_stains", False):
            paper = self._add_coffee_stains(paper)

        if config.get("enable_page_shadows", True):
            paper = self._add_edge_shadow(paper)

        return paper

    def _add_grain(self, paper: Image.Image) -> Image.Image:
        """Add subtle paper grain/fiber texture."""
        arr = np.array(paper, dtype=np.int16)
        noise = np.random.normal(0, 2.5, arr.shape).astype(np.int16)
        result = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(result)

    def _draw_lined(self, draw: ImageDraw.Draw, w: int, h: int, config: Dict):
        """Draw horizontal ruled lines with margin."""
        spacing = config.get("line_spacing", 28)
        line_color = (190, 210, 230, 128)       # Light blue
        margin_color = (240, 130, 130, 100)      # Light red

        # Margin line
        margin_x = int(w * 0.12)  # ~12% from left
        draw.line([(margin_x, 0), (margin_x, h)], fill=margin_color, width=2)

        # Horizontal lines with slight imperfections
        y = spacing + 40  # Start below top margin
        while y < h - 20:
            points = []
            for x in range(0, w, 15):
                jitter = random.uniform(-0.3, 0.3)
                points.append((x, y + jitter))

            if len(points) > 1:
                draw.line(points, fill=line_color, width=1)

            y += spacing

    def _draw_graph(self, draw: ImageDraw.Draw, w: int, h: int, config: Dict):
        """Draw graph paper grid."""
        grid_size = config.get("grid_size", 20)
        line_color = (200, 215, 230, 80)

        # Vertical lines
        for x in range(grid_size, w, grid_size):
            jitter = random.uniform(-0.2, 0.2)
            draw.line([(x + jitter, 0), (x + jitter, h)], fill=line_color, width=1)

        # Horizontal lines
        for y in range(grid_size, h, grid_size):
            jitter = random.uniform(-0.2, 0.2)
            draw.line([(0, y + jitter), (w, y + jitter)], fill=line_color, width=1)

    def _draw_engineering(self, draw: ImageDraw.Draw, w: int, h: int, config: Dict):
        """Draw engineering paper with major/minor grid."""
        minor_size = 5
        major_size = 25
        minor_color = (210, 225, 210, 50)
        major_color = (170, 200, 170, 100)

        # Minor grid
        for x in range(minor_size, w, minor_size):
            draw.line([(x, 0), (x, h)], fill=minor_color, width=1)
        for y in range(minor_size, h, minor_size):
            draw.line([(0, y), (w, y)], fill=minor_color, width=1)

        # Major grid
        for x in range(major_size, w, major_size):
            draw.line([(x, 0), (x, h)], fill=major_color, width=1)
        for y in range(major_size, h, major_size):
            draw.line([(0, y), (w, y)], fill=major_color, width=1)

    def _add_coffee_stains(self, paper: Image.Image) -> Image.Image:
        """Add random subtle coffee stains."""
        overlay = Image.new("RGBA", paper.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        num_stains = random.randint(1, 2)
        for _ in range(num_stains):
            cx = random.randint(100, paper.width - 100)
            cy = random.randint(100, paper.height - 100)
            radius = random.randint(25, 55)

            # Ring shape stain
            for r in range(radius, radius - 8, -1):
                alpha = random.randint(8, 20)
                draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    outline=(139, 90, 43, alpha),
                    width=2,
                )

            # Inner fill (very faint)
            inner_r = radius - 10
            if inner_r > 0:
                draw.ellipse(
                    [(cx - inner_r, cy - inner_r), (cx + inner_r, cy + inner_r)],
                    fill=(139, 90, 43, 8),
                )

        # Composite
        paper_rgba = paper.convert("RGBA")
        composited = Image.alpha_composite(paper_rgba, overlay)
        return composited.convert("RGB")

    def _add_edge_shadow(self, paper: Image.Image) -> Image.Image:
        """Add subtle shadow around page edges."""
        arr = np.array(paper, dtype=np.float32)
        h, w = arr.shape[:2]

        # Create vignette-like gradient
        fade = 40  # pixels of shadow
        for i in range(fade):
            factor = (i / fade) ** 0.5  # Ease-in curve
            darken = 1.0 - (1.0 - factor) * 0.08

            # Top edge
            arr[i, :] *= darken
            # Bottom edge
            arr[h - 1 - i, :] *= darken
            # Left edge
            arr[:, i] *= darken
            # Right edge
            arr[:, w - 1 - i] *= darken

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
