from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    init_db()

    # Create storage directories
    settings.storage_path
    settings.uploads_path
    settings.results_path
    settings.cache_path

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title="Text to Handwriting API",
    description="Convert PDF assignments to realistic handwritten notes with hand-drawn diagrams",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Serve result files
app.mount("/files", StaticFiles(directory=str(settings.storage_path)), name="files")


@app.get("/")
async def root():
    return {
        "name": "Text to Handwriting API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
