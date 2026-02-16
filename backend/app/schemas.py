from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ---------- Enums ----------

class HandwritingStyle(str, Enum):
    CAVEAT = "Caveat"
    INDIE_FLOWER = "Indie Flower"
    PERMANENT_MARKER = "Permanent Marker"
    SHADOWS_INTO_LIGHT = "Shadows Into Light"
    PATRICK_HAND = "Patrick Hand"
    REENIE_BEANIE = "Reenie Beanie"
    COVERED_BY_YOUR_GRACE = "Covered By Your Grace"
    HOMEMADE_APPLE = "Homemade Apple"


class PaperType(str, Enum):
    LINED = "lined"
    GRAPH = "graph"
    BLANK = "blank"
    ENGINEERING = "engineering"


class ExportFormat(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"


# ---------- Request Schemas ----------

class ProcessConfig(BaseModel):
    """Configuration for document processing."""
    handwriting_style: HandwritingStyle = HandwritingStyle.CAVEAT
    imperfection_level: float = Field(default=0.07, ge=0.0, le=0.20)
    paper_type: PaperType = PaperType.LINED
    ink_color: str = Field(default="#1a1a2e", description="Ink color hex")
    line_spacing: int = Field(default=28, ge=20, le=40)
    font_size: int = Field(default=18, ge=12, le=32)
    enable_smudges: bool = True
    enable_coffee_stains: bool = False
    enable_page_shadows: bool = True
    enable_annotations: bool = False


class ProcessRequest(BaseModel):
    """Request to start processing a document."""
    config: ProcessConfig = ProcessConfig()


# ---------- Response Schemas ----------

class UploadResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    pages: int
    message: str = "File uploaded successfully"


class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_stage: str
    num_pages: int
    error_message: Optional[str] = None


class DownloadInfo(BaseModel):
    job_id: str
    filename: str
    format: str
    download_url: str


class JobListResponse(BaseModel):
    jobs: List[dict]
    total: int
