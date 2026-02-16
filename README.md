# Text to Handwriting Web App 📝

Turn typed assignments into realistic handwritten notes with authentic imperfections and hand-drawn diagrams.

## Features

- **Realistic Handwriting**: 8+ styles with adjustable imperfections
- **Paper Textures**: Lined, Graph, Blank, Engineering paper
- **AI Diagrams**: Converts computer charts to hand-drawn sketches (Google Imagen)
- **Modern UI**: Clean, minimal interface built with React + Tailwind
- **Export**: Download as PDF or Images

## Quick Start

### 1. Backend (FastAPI)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API Docs: <http://localhost:8000/docs>

### 2. Frontend (React)

```bash
cd frontend
npm run dev
```

App URL: <http://localhost:5173>

## Configuration

- API Key: Set `GOOGLE_IMAGEN_API_KEY` in `backend/.env` for diagram conversion.
- Database: Uses SQLite `app.db` by default.

## Deployment

See `docker-compose.yml` for containerized deployment.
# T2H
