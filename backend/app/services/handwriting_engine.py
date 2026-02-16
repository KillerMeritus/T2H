"""
Handwriting Engine
Converts text to realistic handwritten format using PIL with imperfections.
"""

from typing import List, Dict, Tuple
from pathlib import Path
import random
import math

from PIL import Image, ImageDraw, ImageFont
import numpy as np


# Font files directory
FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

# Available handwriting fonts (Google Fonts)
FONT_MAP = {
    "Caveat": "Caveat-Regular.ttf",
    "Indie Flower": "IndieFlower-Regular.ttf",
    "Permanent Marker": "PermanentMarker-Regular.ttf",
    "Shadows Into Light": "ShadowsIntoLight-Regular.ttf",
    "Patrick Hand": "PatrickHand-Regular.ttf",
    "Reenie Beanie": "ReenieBeanie-Regular.ttf",
    "Covered By Your Grace": "CoveredByYourGrace-Regular.ttf",
    "Homemade Apple": "HomemadeApple-Regular.ttf",
}


class HandwritingEngine:
    """Converts text to handwritten format with realistic imperfections."""

    def __init__(self, config: Dict):
        self.style = config.get("handwriting_style", "Caveat")
        self.imperfection_level = config.get("imperfection_level", 0.07)
        self.ink_color = self._parse_color(config.get("ink_color", "#1a1a2e"))
        self.font_size = config.get("font_size", 18)
        self.line_spacing = config.get("line_spacing", 28)
        self.enable_smudges = config.get("enable_smudges", True)

        # Load font
        self.font = self._load_font(self.style, self.font_size)
        self.small_font = self._load_font(self.style, int(self.font_size * 0.75))

    def _load_font(self, style: str, size: int) -> ImageFont.FreeTypeFont:
        """Load a handwriting font."""
        font_file = FONT_MAP.get(style, "Caveat-Regular.ttf")
        font_path = FONTS_DIR / font_file

        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)

        # Fallback to default font
        try:
            return ImageFont.truetype("/System/Library/Fonts/Noteworthy.ttc", size)
        except OSError:
            return ImageFont.load_default()

    def _parse_color(self, color_hex: str) -> Tuple[int, int, int]:
        """Parse hex color to RGB tuple."""
        color_hex = color_hex.lstrip("#")
        return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

    def render_page(
        self,
        lines: List[Dict],
        page_width: int,
        page_height: int,
        scale: float = 1.0,
    ) -> Image.Image:
        """
        Render text lines as handwritten text on a transparent canvas.

        Args:
            lines: Text lines with positions
            page_width: Canvas width
            page_height: Canvas height
            scale: DPI scale factor

        Returns:
            PIL RGBA Image with handwritten text
        """
        # Create transparent canvas
        canvas_w = int(page_width * scale)
        canvas_h = int(page_height * scale)
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        for line in lines:
            # Apply imperfections to text
            processed = self._apply_imperfections(line["text"])

            # Calculate Y position with slight variation
            y = int(line["y"] * scale) + random.uniform(-1, 1)
            x_start = int(line.get("x", 80) * scale)

            # Render processed text
            self._render_line(draw, processed, x_start, y, scale)

        # Apply global effects
        if self.enable_smudges:
            canvas = self._apply_smudges(canvas)

        return canvas

    def _apply_imperfections(self, text: str) -> List[Dict]:
        """
        Apply realistic writing imperfections.

        Returns list of text segments with rendering instructions.
        """
        words = text.split()
        segments = []

        for word in words:
            if not word.strip():
                segments.append({"text": " ", "type": "normal"})
                continue

            roll = random.random()

            if roll < self.imperfection_level and len(word) > 2:
                # Choose mistake type
                mistake = random.choices(
                    ["spelling", "strikethrough", "erasure"],
                    weights=[0.4, 0.4, 0.2],
                    k=1
                )[0]

                if mistake == "spelling":
                    misspelled = self._make_spelling_error(word)
                    segments.append({
                        "text": misspelled,
                        "type": "error",
                        "correction": word,
                    })
                elif mistake == "strikethrough":
                    segments.append({
                        "text": word,
                        "type": "strikethrough",
                        "correction": word,
                    })
                else:
                    segments.append({
                        "text": word,
                        "type": "erasure",
                    })
            else:
                segments.append({"text": word, "type": "normal"})

        return segments

    def _make_spelling_error(self, word: str) -> str:
        """Generate a realistic spelling mistake."""
        if len(word) < 3:
            return word

        error_type = random.choice(["swap", "double", "miss", "nearby"])

        try:
            if error_type == "swap" and len(word) >= 3:
                pos = random.randint(1, len(word) - 2)
                return word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]

            elif error_type == "double":
                pos = random.randint(0, len(word) - 1)
                return word[:pos] + word[pos] + word[pos:]

            elif error_type == "miss" and len(word) >= 4:
                pos = random.randint(1, len(word) - 2)
                return word[:pos] + word[pos + 1:]

            elif error_type == "nearby":
                nearby = {
                    "a": "s", "s": "a", "d": "s", "e": "r", "r": "t",
                    "t": "y", "i": "o", "o": "p", "n": "m", "m": "n",
                }
                pos = random.randint(0, len(word) - 1)
                ch = word[pos].lower()
                replacement = nearby.get(ch, ch)
                if word[pos].isupper():
                    replacement = replacement.upper()
                return word[:pos] + replacement + word[pos + 1:]
        except (IndexError, ValueError):
            pass

        return word

    def _render_line(
        self, draw: ImageDraw.Draw, segments: List[Dict],
        x: float, y: float, scale: float
    ):
        """Render a single line of handwritten text."""
        cursor_x = x

        for segment in segments:
            text = segment["text"]
            seg_type = segment["type"]

            # Position jitter
            jx = random.uniform(-2, 2) * scale
            jy = random.uniform(-1.5, 1.5) * scale

            # Pressure variation -> opacity
            pressure = random.uniform(0.75, 1.0)
            alpha = int(255 * pressure)
            ink = (*self.ink_color, alpha)

            pos_x = cursor_x + jx
            pos_y = y + jy

            if seg_type == "strikethrough":
                # Draw word
                draw.text((pos_x, pos_y), text, font=self.font, fill=ink)
                bbox = draw.textbbox((pos_x, pos_y), text, font=self.font)

                # Draw strikethrough with slight waviness
                mid_y = (bbox[1] + bbox[3]) / 2
                points = []
                for px in range(int(bbox[0] - 3), int(bbox[2] + 3), 4):
                    wave = random.uniform(-1.5, 1.5)
                    points.append((px, mid_y + wave))
                if len(points) > 1:
                    draw.line(points, fill=(*self.ink_color, 200), width=2)

                # Write correction above
                corr_y = bbox[1] - self.font_size * scale - 2
                corr_ink = (*self.ink_color, int(alpha * 0.9))
                draw.text(
                    (pos_x + random.uniform(-3, 3), corr_y),
                    segment["correction"],
                    font=self.small_font,
                    fill=corr_ink,
                )

            elif seg_type == "error":
                # Draw misspelled word
                draw.text((pos_x, pos_y), text, font=self.font, fill=ink)
                bbox = draw.textbbox((pos_x, pos_y), text, font=self.font)

                # Draw light strikethrough on misspelling
                mid_y = (bbox[1] + bbox[3]) / 2
                draw.line(
                    [(bbox[0], mid_y), (bbox[2], mid_y)],
                    fill=(*self.ink_color, 150),
                    width=1,
                )

                # Write correct word above
                corr_y = bbox[1] - self.font_size * scale - 2
                draw.text(
                    (pos_x + random.uniform(-2, 2), corr_y),
                    segment["correction"],
                    font=self.small_font,
                    fill=(*self.ink_color, int(alpha * 0.9)),
                )

            elif seg_type == "erasure":
                # Draw faded text (like erased then written over)
                faded_ink = (*self.ink_color, 60)
                draw.text((pos_x, pos_y), text, font=self.font, fill=faded_ink)
                # Rewrite slightly offset
                draw.text(
                    (pos_x + random.uniform(1, 3), pos_y + random.uniform(-1, 1)),
                    text,
                    font=self.font,
                    fill=ink,
                )

            else:
                # Normal text
                draw.text((pos_x, pos_y), text, font=self.font, fill=ink)

            # Advance cursor with variable spacing
            bbox = draw.textbbox((pos_x, pos_y), text, font=self.font)
            word_width = bbox[2] - bbox[0]
            cursor_x += word_width + random.uniform(4, 8) * scale

    def _apply_smudges(self, image: Image.Image) -> Image.Image:
        """Apply subtle ink smudge effects."""
        img_array = np.array(image)

        # Random smudge spots (very subtle)
        num_smudges = random.randint(0, 3)
        for _ in range(num_smudges):
            sx = random.randint(50, image.width - 50)
            sy = random.randint(50, image.height - 50)
            radius = random.randint(3, 8)

            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        px, py = sx + dx, sy + dy
                        if 0 <= px < image.width and 0 <= py < image.height:
                            if img_array[py, px, 3] > 0:  # Only smudge where there's ink
                                img_array[py, px, 3] = min(
                                    255, img_array[py, px, 3] + random.randint(0, 20)
                                )

        return Image.fromarray(img_array)
