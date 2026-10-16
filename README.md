# CareerAI — CV Optimizer & Interview Coach

An AI-powered full-stack platform that tailors CVs to specific job descriptions and provides an Interview Coach to generate role-specific questions, evaluate answers, and deliver detailed performance feedback.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + Tailwind CSS |
| Backend | Python 3.11 + FastAPI |
| AI | Ollama + Llama 3 (local) |
| PDF Parsing | PyMuPDF |
| Database | SQLite |
| Storage | Local filesystem (dev) / AWS S3 (extend later) |
| Deployment | Docker + Docker Compose |

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- Ollama installed and running → [ollama.com](https://ollama.com)
- Llama 3 model pulled: `ollama pull llama3`

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Ensure Ollama is running: ollama serve

# Run backend
uvicorn app.main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## Environment Variables

Copy `.env.example` to `backend/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name (default: `llama3`) |
| `SECRET_KEY` | JWT signing secret (any random string) |
| `DATABASE_URL` | SQLite URL |
| `UPLOAD_DIR` | Directory for CV file uploads |
| `FRONTEND_URL` | Frontend URL for CORS |

---

## Docker Deployment

```bash
# Copy and configure env
copy .env.example .env
# Edit .env with your SECRET_KEY
# Ensure Ollama is running on the host: ollama serve

# Build and run all services
docker-compose up --build

# App available at http://localhost:3000
# API docs at http://localhost:8000/docs
```

---

## Features

### CV Optimizer
- Upload PDF CV → automatic text extraction with PyMuPDF
- Provide a job description → AI rewrites the CV to match
- Match score (0-100) with color-coded gauge
- Missing keywords detection
- Side-by-side original vs optimized comparison
- Manage multiple CVs

### Interview Coach
- Provide a job title + description (optionally attach a CV for context)
- AI generates 5–15 role-specific questions across categories:
  - **Behavioral** — past experience & soft skills
  - **Technical** — domain-specific knowledge
  - **Situational** — hypothetical scenarios
- Submit answers → instant AI feedback with score, strengths, improvements
- Complete session → comprehensive performance report with category breakdown

---

## Project Structure

```
software CV/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, JWT security
│   │   ├── db/            # SQLAlchemy engine, init
│   │   ├── models/        # User, CV, Interview models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── routers/       # auth, cv, interview API endpoints
│   │   ├── services/      # ai_service, pdf_service, storage_service
│   │   └── main.py        # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Sidebar, FileUpload, ScoreGauge, etc.
│   │   ├── context/       # AuthContext
│   │   ├── pages/         # Landing, Dashboard, CV*, Interview*
│   │   ├── services/      # api.js (Axios client)
│   │   ├── App.jsx        # Router + layout
│   │   └── index.css      # Tailwind + global styles
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/cv/upload` | Upload PDF CV |
| GET | `/api/cv/list` | List user CVs |
| GET | `/api/cv/{id}` | Get CV details |
| POST | `/api/cv/optimize` | AI-optimize CV |
| DELETE | `/api/cv/{id}` | Delete CV |
| POST | `/api/interview/start` | Start session, generate questions |
| GET | `/api/interview/sessions` | List sessions |
| GET | `/api/interview/{id}` | Get session + questions |
| POST | `/api/interview/{id}/answer/{qid}` | Submit answer, get feedback |
| POST | `/api/interview/{id}/complete` | Complete + generate report |
