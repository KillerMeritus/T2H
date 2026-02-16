"""
Export Service
Generates final output files (PDF, PNG, JPG).
"""

from typing import List
from pathlib import Path
import io

from PIL import Image
from fpdf import FPDF


class ExportService:
    """Handles exporting composed pages to various formats."""

    def export_pdf(self, pages: List[Image.Image], output_path: str):
        """
        Export composed pages as a multi-page PDF.

        Args:
            pages: List of PIL Images (one per page)
            output_path: Path to save the PDF
        """
        if not pages:
            return

        # Get page dimensions from first page
        first = pages[0]
        w_mm = first.width * 25.4 / 150  # pixel to mm at 150 DPI
        h_mm = first.height * 25.4 / 150

        pdf = FPDF(unit="mm", format=(w_mm, h_mm))

        for i, page_img in enumerate(pages):
            pdf.add_page()

            # Save temp image
            temp_path = Path(output_path).parent / f"_temp_page_{i}.jpg"
            page_img.save(str(temp_path), "JPEG", quality=95)

            # Add to PDF
            pdf.image(str(temp_path), x=0, y=0, w=w_mm, h=h_mm)

            # Clean temp
            temp_path.unlink(missing_ok=True)

        pdf.output(output_path)

    def export_images(
        self, pages: List[Image.Image], output_dir: str, fmt: str = "png"
    ) -> List[str]:
        """
        Export pages as individual images.

        Returns list of output file paths.
        """
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        paths = []

        for i, page_img in enumerate(pages):
            filename = f"page_{i + 1}.{fmt}"
            file_path = output / filename

            if fmt.lower() == "jpg" or fmt.lower() == "jpeg":
                # Convert RGBA to RGB for JPEG
                if page_img.mode == "RGBA":
                    bg = Image.new("RGB", page_img.size, (255, 255, 255))
                    bg.paste(page_img, mask=page_img.split()[3])
                    page_img = bg
                page_img.save(str(file_path), "JPEG", quality=95)
            else:
                page_img.save(str(file_path), "PNG")

            paths.append(str(file_path))

        return paths
