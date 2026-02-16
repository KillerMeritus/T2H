import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Enum, Float
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from app.database import Base


class JobStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Tracks PDF processing jobs."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default=JobStatus.UPLOADED.value)
    config = Column(JSON, nullable=True)
    num_pages = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    current_stage = Column(String(100), default="")
    upload_path = Column(String(512), nullable=True)
    result_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "config": self.config,
            "num_pages": self.num_pages,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class DiagramCache(Base):
    """Caches AI-converted diagrams to avoid repeated API calls."""
    __tablename__ = "diagram_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_hash = Column(String(64), unique=True, index=True, nullable=False)
    diagram_type = Column(String(50), default="generic")
    original_path = Column(String(512), nullable=False)
    converted_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
