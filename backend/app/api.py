from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import shutil
import uuid

from app.database import get_db
from app.models import Job, JobStatus
from app.schemas import (
    ProcessConfig, ProcessRequest, UploadResponse,
    ProcessResponse, StatusResponse, ExportFormat
)
from app.config import settings
from app.services.processor import process_document_task

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF file for processing."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Create job
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        filename=file.filename,
        status=JobStatus.UPLOADED.value,
    )
    db.add(job)
    db.commit()

    # Save file
    upload_dir = settings.uploads_path / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / "original.pdf"

    with open(file_path, "wb") as f:
        f.write(content)

    job.upload_path = str(file_path)

    # Get page count
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(file_path))
        job.num_pages = len(reader.pages)
    except Exception:
        job.num_pages = 0

    db.commit()

    return UploadResponse(
        job_id=job_id,
        status=job.status,
        filename=file.filename,
        pages=job.num_pages,
    )


@router.post("/process/{job_id}", response_model=ProcessResponse)
async def process_document(
    job_id: str,
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start processing an uploaded PDF document."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.PROCESSING.value:
        raise HTTPException(status_code=400, detail="Job is already processing")

    if job.status == JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Job already completed")

    # Update job with config
    job.config = request.config.model_dump()
    job.status = JobStatus.PROCESSING.value
    job.progress = 0
    job.current_stage = "Starting..."
    db.commit()

    # Queue background processing
    background_tasks.add_task(
        process_document_task,
        job_id=job_id,
        config=request.config.model_dump(),
    )

    return ProcessResponse(
        job_id=job_id,
        status="processing",
        message="Processing started. Use /status endpoint to track progress.",
    )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """Get processing status for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return StatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage or "",
        num_pages=job.num_pages or 0,
        error_message=job.error_message,
    )


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    format: ExportFormat = ExportFormat.PDF,
    db: Session = Depends(get_db),
):
    """Download the processed result."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Job not yet completed")

    result_path = Path(job.result_path) if job.result_path else None

    if not result_path or not result_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    # Determine filename
    original_name = Path(job.filename).stem
    download_name = f"handwritten_{original_name}.{format.value}"

    return FileResponse(
        path=str(result_path),
        filename=download_name,
        media_type="application/pdf" if format == ExportFormat.PDF else f"image/{format.value}",
    )


@router.get("/preview/{job_id}/{page_num}")
async def get_preview(
    job_id: str,
    page_num: int,
    db: Session = Depends(get_db),
):
    """Get preview image for a specific page."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Job not yet completed")

    preview_dir = settings.results_path / job_id / "preview"
    preview_path = preview_dir / f"page_{page_num}.png"

    if not preview_path.exists():
        raise HTTPException(status_code=404, detail=f"Preview for page {page_num} not found")

    return FileResponse(path=str(preview_path), media_type="image/png")


@router.get("/jobs")
async def list_jobs(db: Session = Depends(get_db)):
    """List all jobs."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": len(jobs),
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its files."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete files
    upload_dir = settings.uploads_path / job_id
    result_dir = settings.results_path / job_id

    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    if result_dir.exists():
        shutil.rmtree(result_dir)

    # Delete from DB
    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully"}
