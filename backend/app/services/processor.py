"""
Main Document Processor
Orchestrates the full PDF-to-handwriting conversion pipeline.
Runs as a background task triggered by the API.
"""

from typing import Dict
from pathlib import Path
from datetime import datetime
import traceback

from PIL import Image

from app.database import SessionLocal
from app.models import Job, JobStatus
from app.config import settings
from app.services.pdf_processor import PDFProcessor
from app.services.handwriting_engine import HandwritingEngine
from app.services.paper_renderer import PaperRenderer
from app.services.diagram_converter import DiagramConverter
from app.services.layout_composer import LayoutComposer
from app.services.export_service import ExportService


def _update_job(db, job_id: str, **kwargs):
    """Helper to update job status in database."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        job.updated_at = datetime.utcnow()
        db.commit()


async def process_document_task(job_id: str, config: Dict):
    """
    Background task: full document processing pipeline.

    Steps:
        1. Extract text and images from PDF
        2. Generate paper background
        3. Convert text to handwriting
        4. Convert diagrams via AI (if any)
        5. Compose all layers
        6. Export as PDF + preview images
    """
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        pdf_path = job.upload_path
        if not pdf_path or not Path(pdf_path).exists():
            _update_job(db, job_id, status=JobStatus.FAILED.value,
                        error_message="PDF file not found")
            return

        # Initialize services
        pdf_processor = PDFProcessor()
        handwriting = HandwritingEngine(config)
        paper_renderer = PaperRenderer()
        diagram_converter = DiagramConverter(db=db)
        layout_composer = LayoutComposer()
        export_service = ExportService()

        # Get PDF info
        pdf_info = pdf_processor.get_info(pdf_path)
        num_pages = pdf_info["num_pages"]

        _update_job(db, job_id, progress=5, current_stage="Extracting PDF content...")

        # DPI scale factor
        dpi = 150
        scale = dpi / 72.0  # PDF points to pixels

        composed_pages = []

        for page_num in range(1, num_pages + 1):
            page_progress_base = int(5 + (page_num - 1) / num_pages * 80)

            # ── Step 1: Extract page data ──
            _update_job(
                db, job_id,
                progress=page_progress_base,
                current_stage=f"Extracting page {page_num}/{num_pages}..."
            )
            page_data = pdf_processor.extract_page_data(pdf_path, page_num)

            page_w = int(page_data["width"] * scale)
            page_h = int(page_data["height"] * scale)

            # ── Step 2: Render paper background ──
            _update_job(
                db, job_id,
                progress=page_progress_base + 5,
                current_stage=f"Rendering paper for page {page_num}..."
            )
            paper = paper_renderer.render(
                paper_type=config.get("paper_type", "lined"),
                width=page_w,
                height=page_h,
                config=config,
            )

            # ── Step 3: Convert text to handwriting ──
            _update_job(
                db, job_id,
                progress=page_progress_base + 10,
                current_stage=f"Writing text on page {page_num}..."
            )
            text_layer = handwriting.render_page(
                lines=page_data["lines"],
                page_width=page_data["width"],
                page_height=page_data["height"],
                scale=scale,
            )

            # ── Step 4: Convert diagrams ──
            converted_diagrams = []
            if page_data["images"]:
                _update_job(
                    db, job_id,
                    progress=page_progress_base + 15,
                    current_stage=f"Converting diagrams on page {page_num}..."
                )
                # Extract actual diagram image data
                extracted = pdf_processor.extract_diagram_images(
                    pdf_path, page_num, page_data["images"]
                )
                if extracted:
                    converted_diagrams = await diagram_converter.convert_diagrams(extracted)

            # ── Step 5: Compose page ──
            _update_job(
                db, job_id,
                progress=page_progress_base + 18,
                current_stage=f"Composing page {page_num}..."
            )
            composed = layout_composer.compose_page(
                paper=paper,
                text_layer=text_layer,
                diagrams=converted_diagrams,
                scale=scale,
            )
            composed_pages.append(composed)

        # ── Step 6: Export ──
        _update_job(db, job_id, progress=90, current_stage="Generating output files...")

        result_dir = settings.results_path / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        # Save preview images
        preview_dir = result_dir / "preview"
        preview_dir.mkdir(parents=True, exist_ok=True)

        for i, page_img in enumerate(composed_pages):
            preview_path = preview_dir / f"page_{i + 1}.png"
            page_img.save(str(preview_path), "PNG", quality=95)

        # Generate PDF
        pdf_output_path = result_dir / "result.pdf"
        export_service.export_pdf(composed_pages, str(pdf_output_path))

        # ── Done ──
        _update_job(
            db, job_id,
            status=JobStatus.COMPLETED.value,
            progress=100,
            current_stage="Completed",
            result_path=str(pdf_output_path),
            completed_at=datetime.utcnow(),
        )

    except Exception as e:
        traceback.print_exc()
        _update_job(
            db, job_id,
            status=JobStatus.FAILED.value,
            current_stage="Failed",
            error_message=str(e),
        )

    finally:
        db.close()
