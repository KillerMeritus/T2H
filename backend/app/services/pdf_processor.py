"""
PDF Processing Service
Extracts text with positions, images, and layout data from PDF files.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import io
import hashlib

import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import numpy as np


class PDFProcessor:
    """Extracts all content from PDF files while preserving layout."""

    def __init__(self):
        self.dpi = 150  # Resolution for rendering

    def get_info(self, pdf_path: str) -> Dict:
        """Get basic PDF metadata."""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return {
                "num_pages": len(reader.pages),
                "title": reader.metadata.get("/Title", "") if reader.metadata else "",
            }

    def extract_page_data(self, pdf_path: str, page_num: int) -> Dict:
        """
        Extract all data from a single page.

        Returns:
            {
                'page_num': int,
                'width': float,
                'height': float,
                'text_elements': List[TextElement],
                'images': List[ImageElement],
                'lines': List[LineGroup]  # grouped text lines
            }
        """
        text_elements = self._extract_text(pdf_path, page_num)
        images = self._extract_images(pdf_path, page_num)
        page_size = self._get_page_size(pdf_path, page_num)

        # Group text into lines
        lines = self._group_into_lines(text_elements)

        return {
            "page_num": page_num,
            "width": page_size[0],
            "height": page_size[1],
            "text_elements": text_elements,
            "images": images,
            "lines": lines,
        }

    def _get_page_size(self, pdf_path: str, page_num: int) -> Tuple[float, float]:
        """Get page dimensions."""
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]
            return (page.width, page.height)

    def _extract_text(self, pdf_path: str, page_num: int) -> List[Dict]:
        """Extract text words with positions."""
        elements = []

        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=True,
                extra_attrs=["fontname", "size"],
            )

            for word in words:
                elements.append({
                    "text": word["text"],
                    "x": float(word["x0"]),
                    "y": float(word["top"]),
                    "width": float(word["x1"] - word["x0"]),
                    "height": float(word["bottom"] - word["top"]),
                    "font_size": float(word.get("size", 12)),
                    "font_name": word.get("fontname", ""),
                    "is_math": self._detect_math(word["text"]),
                })

        return elements

    def _extract_images(self, pdf_path: str, page_num: int) -> List[Dict]:
        """Extract embedded images from a page."""
        images = []

        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]

            if hasattr(page, "images") and page.images:
                for i, img_info in enumerate(page.images):
                    try:
                        # Get image bounds
                        x0 = float(img_info.get("x0", 0))
                        y0 = float(img_info.get("top", 0))
                        x1 = float(img_info.get("x1", 0))
                        y1 = float(img_info.get("bottom", 0))

                        images.append({
                            "index": i,
                            "x": x0,
                            "y": y0,
                            "width": x1 - x0,
                            "height": y1 - y0,
                            "page_num": page_num,
                        })
                    except Exception as e:
                        print(f"Warning: Could not extract image {i} from page {page_num}: {e}")

        return images

    def render_page_image(self, pdf_path: str, page_num: int) -> Image.Image:
        """Render a PDF page as a PIL Image."""
        images = convert_from_path(
            pdf_path,
            first_page=page_num,
            last_page=page_num,
            dpi=self.dpi,
        )
        return images[0] if images else None

    def extract_diagram_images(
        self, pdf_path: str, page_num: int, image_regions: List[Dict]
    ) -> List[Dict]:
        """
        Extract diagram regions from a rendered page image.

        Renders the page and crops out diagram regions.
        """
        if not image_regions:
            return []

        # Render full page
        page_image = self.render_page_image(pdf_path, page_num)
        if not page_image:
            return []

        # Get page dimensions for coordinate mapping
        page_size = self._get_page_size(pdf_path, page_num)
        scale_x = page_image.width / page_size[0]
        scale_y = page_image.height / page_size[1]

        extracted = []
        for region in image_regions:
            try:
                # Map PDF coordinates to image coordinates
                left = int(region["x"] * scale_x)
                top = int(region["y"] * scale_y)
                right = int((region["x"] + region["width"]) * scale_x)
                bottom = int((region["y"] + region["height"]) * scale_y)

                # Ensure bounds are valid
                left = max(0, left)
                top = max(0, top)
                right = min(page_image.width, right)
                bottom = min(page_image.height, bottom)

                if right > left and bottom > top:
                    cropped = page_image.crop((left, top, right, bottom))

                    # Convert to bytes for hashing/storage
                    buf = io.BytesIO()
                    cropped.save(buf, format="PNG")
                    img_bytes = buf.getvalue()

                    extracted.append({
                        "image": cropped,
                        "image_bytes": img_bytes,
                        "image_hash": hashlib.sha256(img_bytes).hexdigest(),
                        "x": region["x"],
                        "y": region["y"],
                        "width": region["width"],
                        "height": region["height"],
                    })
            except Exception as e:
                print(f"Warning: Failed to extract diagram: {e}")

        return extracted

    def _group_into_lines(self, text_elements: List[Dict]) -> List[Dict]:
        """Group text elements into lines based on Y position."""
        if not text_elements:
            return []

        # Sort by Y position
        sorted_elements = sorted(text_elements, key=lambda e: (e["y"], e["x"]))

        lines = []
        current_line = [sorted_elements[0]]
        current_y = sorted_elements[0]["y"]

        for elem in sorted_elements[1:]:
            # Same line if Y difference is small
            if abs(elem["y"] - current_y) < 5:
                current_line.append(elem)
            else:
                # Sort line by X position
                current_line.sort(key=lambda e: e["x"])
                line_text = " ".join(e["text"] for e in current_line)
                lines.append({
                    "text": line_text,
                    "y": current_y,
                    "x": current_line[0]["x"],
                    "elements": current_line,
                    "font_size": current_line[0]["font_size"],
                })
                current_line = [elem]
                current_y = elem["y"]

        # Don't forget last line
        if current_line:
            current_line.sort(key=lambda e: e["x"])
            line_text = " ".join(e["text"] for e in current_line)
            lines.append({
                "text": line_text,
                "y": current_y,
                "x": current_line[0]["x"],
                "elements": current_line,
                "font_size": current_line[0]["font_size"],
            })

        return lines

    def _detect_math(self, text: str) -> bool:
        """Check if text contains mathematical notation."""
        math_chars = set("=+−×÷∫∑√∞≤≥≠±∂∇αβγδεθλμπσφψω²³⁴")
        return bool(set(text) & math_chars)
