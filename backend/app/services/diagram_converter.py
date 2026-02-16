"""
Diagram Converter
Converts extracted diagrams to hand-drawn style using Google Imagen API.
Transparent background so diagrams blend with paper texture.
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import hashlib
import io
import base64
import asyncio

import httpx
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DiagramCache


class DiagramConverter:
    """Converts diagrams to hand-drawn style using AI."""

    # Prompt templates – TRANSPARENT background for all
    BASE_PROMPT = (
        "Convert this diagram to a hand-drawn sketch with TRANSPARENT BACKGROUND. "
        "No paper background, no white background. Only the hand-drawn lines, labels, "
        "and elements should be visible. Make it look naturally drawn with pencil/pen, "
        "slightly imperfect lines, like a student drew it."
    )

    TYPE_PROMPTS = {
        "circuit": " Use pencil style, hand-drawn circuit symbols (resistors, capacitors, wires), slightly imperfect lines.",
        "flowchart": " Pen style, hand-drawn boxes with rounded corners, natural arrows, slight size variations.",
        "graph": " Pencil drawn axes and curves, natural mathematical notation, hand-labeled axes.",
        "chemistry": " Hand-drawn molecular structures, bond lines, chemical symbols in handwriting.",
        "biology": " Hand-drawn anatomical sketch with labels and arrows, natural biological illustration.",
        "math": " Hand-drawn geometric shapes, equations, labeled points, pencil style.",
        "generic": " Sketchy natural hand-drawn appearance, pencil/pen style.",
    }

    def __init__(self, db: Optional[Session] = None):
        self.api_key = settings.GOOGLE_IMAGEN_API_KEY
        self.project_id = settings.GOOGLE_PROJECT_ID
        self.location = settings.GOOGLE_LOCATION
        self.db = db
        self.cache_dir = settings.cache_path / "diagrams"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def convert_diagrams(self, diagrams: List[Dict]) -> List[Dict]:
        """
        Convert a list of diagrams to hand-drawn style.

        Each diagram dict should have:
            - image_bytes: raw bytes
            - image_hash: sha256 hash
            - x, y, width, height: position on page

        Returns list with added 'converted_image' (PIL Image).
        """
        results = []

        for diagram in diagrams:
            converted = await self._convert_single(diagram)
            results.append(converted)

        return results

    async def _convert_single(self, diagram: Dict) -> Dict:
        """Convert a single diagram, checking cache first."""
        img_hash = diagram["image_hash"]

        # 1. Check file cache
        cached_path = self.cache_dir / f"{img_hash}.png"
        if cached_path.exists():
            converted_img = Image.open(cached_path).convert("RGBA")
            diagram["converted_image"] = converted_img
            diagram["from_cache"] = True
            return diagram

        # 2. Check DB cache
        if self.db:
            cache_entry = (
                self.db.query(DiagramCache)
                .filter(DiagramCache.image_hash == img_hash)
                .first()
            )
            if cache_entry and Path(cache_entry.converted_path).exists():
                converted_img = Image.open(cache_entry.converted_path).convert("RGBA")
                diagram["converted_image"] = converted_img
                diagram["from_cache"] = True
                cache_entry.last_accessed = datetime.utcnow()
                self.db.commit()
                return diagram

        # 3. Call AI API
        if not self.api_key or self.api_key == "your_api_key_here":
            # No API key – return original as-is
            diagram["converted_image"] = diagram.get("image", diagram.get("image_bytes"))
            diagram["warning"] = "No Imagen API key configured. Using original diagram."
            return diagram

        diagram_type = self._detect_type(diagram)
        converted_img = await self._call_imagen(diagram, diagram_type)

        if converted_img:
            # Save to cache
            converted_img.save(str(cached_path), "PNG")

            if self.db:
                # Save original too
                orig_path = self.cache_dir / f"{img_hash}_original.png"
                if "image" in diagram:
                    diagram["image"].save(str(orig_path), "PNG")

                cache_entry = DiagramCache(
                    image_hash=img_hash,
                    diagram_type=diagram_type,
                    original_path=str(orig_path),
                    converted_path=str(cached_path),
                )
                self.db.add(cache_entry)
                self.db.commit()

            diagram["converted_image"] = converted_img
        else:
            # Fallback: use original
            if "image" in diagram:
                diagram["converted_image"] = diagram["image"]
            diagram["warning"] = "AI conversion failed. Using original."

        return diagram

    def _detect_type(self, diagram: Dict) -> str:
        """Simple heuristic to detect diagram type."""
        # For now, return generic. Can be enhanced with OpenCV or ML.
        return "generic"

    def _generate_prompt(self, diagram_type: str) -> str:
        """Build the full prompt for Imagen API."""
        type_suffix = self.TYPE_PROMPTS.get(diagram_type, self.TYPE_PROMPTS["generic"])
        return self.BASE_PROMPT + type_suffix

    async def _call_imagen(self, diagram: Dict, diagram_type: str) -> Optional[Image.Image]:
        """Call Google Imagen API for image-to-image conversion."""
        prompt = self._generate_prompt(diagram_type)

        # Encode image
        if "image_bytes" in diagram:
            img_base64 = base64.b64encode(diagram["image_bytes"]).decode("utf-8")
        elif "image" in diagram:
            buf = io.BytesIO()
            diagram["image"].save(buf, format="PNG")
            img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        else:
            return None

        url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/imagen-3.0-generate-001:predict"
        )

        request_body = {
            "instances": [{
                "prompt": prompt,
                "image": {"bytesBase64Encoded": img_base64},
            }],
            "parameters": {
                "sampleCount": 1,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        url,
                        json=request_body,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "predictions" in data and data["predictions"]:
                            img_b64 = data["predictions"][0].get("bytesBase64Encoded", "")
                            if img_b64:
                                img_bytes = base64.b64decode(img_b64)
                                return Image.open(io.BytesIO(img_bytes)).convert("RGBA")

                    elif response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    else:
                        print(f"Imagen API error {response.status_code}: {response.text[:200]}")
                        break

                except Exception as e:
                    print(f"Imagen API call failed (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)

        return None
