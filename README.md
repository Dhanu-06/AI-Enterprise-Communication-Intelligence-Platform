# AI Enterprise Communication Intelligence Platform

Enterprise platform for ingesting ZIP email archives, parsing metadata, storing records in PostgreSQL, indexing in Elasticsearch, semantic search with ChromaDB + LangChain embeddings, AI summaries, thread reconstruction, analytics, and similar-email recommendations.

> **Start here:** [QUICKSTART.md](QUICKSTART.md) — full step-by-step run guide for Windows.

## Architecture

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL 16 |
| Keyword search | Elasticsearch 8.17 |
| Semantic search | ChromaDB 0.5.23 (HTTP server) |
| Embeddings | LangChain + Sentence Transformers |
| Orchestration | Docker Compose |

## Prerequisites

- **Docker Desktop** (Windows/Mac) with at least **8 GB RAM** allocated
- **Git** (optional)

> **Windows tip:** If Elasticsearch fails to start, run in an elevated PowerShell:
> `wsl -d docker-desktop sysctl -w vm.max_map_count=262144`

---

## Option A — Full stack with Docker (recommended)

One command starts PostgreSQL, Elasticsearch, ChromaDB, backend, and frontend.

### PowerShell (Windows)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"

# 1. Create environment file
copy .env.example .env

# 2. Start everything (first build: 10–20 minutes — downloads ML models)
.\scripts\start.ps1

# Or manually:
docker compose up -d --build
```

### Bash (Linux/macOS)

```bash
cd /path/to/AI-integration
cp .env.example .env
chmod +x scripts/start.sh
./scripts/start.sh
```

### URLs after startup

| Service | URL |
|---------|-----|
| **Web UI** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **Swagger docs** | http://localhost:8000/docs |
| **Health check** | http://localhost:8000/api/v1/health |
| **Elasticsearch** | http://localhost:9200 |
| **ChromaDB** | http://localhost:8001 |

### Useful Docker commands

```powershell
# View backend logs (model download, migrations, ingestion)
docker compose logs -f backend

# View all service status
docker compose ps

# Stop all services
docker compose down

# Stop and remove volumes (fresh database)
docker compose down -v
```

### First-time usage

1. Open http://localhost:3000
2. Go to **Upload** → upload a `.zip` of `.eml` email files
3. Wait for processing (status updates every few seconds)
4. Use **Search** (semantic or keyword), **Emails**, and **Analytics**

---

## Option B — Local development (infra in Docker, apps on host)

Run databases/search in Docker; run backend and frontend locally for faster iteration.

### 1. Start infrastructure

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"

docker network create comm_intel_network 2>$null

docker compose -f docker/docker-compose.postgres.yml up -d
docker compose -f docker/docker-compose.elasticsearch.yml up -d
docker compose -f docker/docker-compose.chroma.yml up -d
```

### 2. Backend

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

copy .env.example .env
# Edit .env if needed — defaults work with Docker infra above

.\scripts\setup_database.ps1
# Or: alembic upgrade head

# Initialize search indexes (after ES + Chroma are up)
python scripts/verify_elasticsearch.py --template
.\scripts\setup_vectors.ps1

# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend (new terminal)

```powershell
cd frontend

npm install
copy .env.example .env.local

npm run dev
```

Open http://localhost:3000

---

## Option C — Infrastructure only scripts

| Script | Purpose |
|--------|---------|
| `backend\scripts\setup_database.ps1` | PostgreSQL + Alembic migrations |
| `backend\scripts\setup_elasticsearch.ps1` | Elasticsearch + index template |
| `backend\scripts\setup_vectors.ps1` | ChromaDB (HTTP Docker) + reindex |
| `backend\scripts\setup_chroma.ps1 -Mode http` | Chroma server only |
| `backend\scripts\reindex_elasticsearch.py` | Rebuild ES index from PostgreSQL |
| `backend\scripts\reindex_chroma.py` | Rebuild Chroma vectors from PostgreSQL |

---

## API endpoints (summary)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/uploads` | Upload ZIP archive |
| `GET` | `/api/v1/emails` | List emails |
| `GET` | `/api/v1/emails/{id}` | Email detail + similar emails |
| `POST` | `/api/v1/search/keyword` | Elasticsearch search |
| `POST` | `/api/v1/search/semantic` | ChromaDB semantic search |
| `GET` | `/api/v1/search/similar/{id}` | Similar email recommendations |
| `GET` | `/api/v1/analytics/dashboard` | Analytics data |
| `GET` | `/api/v1/health` | System health |

---

## Project structure

```
AI integration/
├── docker-compose.yml          # Full stack
├── docker/                     # Per-service compose files (dev)
├── backend/                    # FastAPI application
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Next.js application
│   ├── src/
│   └── Dockerfile
└── scripts/
    ├── start.ps1
    └── stop.ps1
```

---

## Environment variables

| File | Used by |
|------|---------|
| `.env` (root) | Docker Compose ports & build args |
| `backend/.env` | Local backend development |
| `backend/.env.docker` | Backend container |
| `frontend/.env.local` | Local Next.js (`NEXT_PUBLIC_API_URL`) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Backend `unhealthy` on first start | Wait 5–10 min for HuggingFace model download; check `docker compose logs backend` |
| Elasticsearch won't start | Increase Docker memory; set `vm.max_map_count` (see above) |
| Frontend can't reach API | Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` |
| Chroma search empty | Run `python backend/scripts/reindex_chroma.py` after uploading emails |
| Port already in use | Change ports in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`, etc.) |

---

## License

MIT (adjust as needed for your organization).
