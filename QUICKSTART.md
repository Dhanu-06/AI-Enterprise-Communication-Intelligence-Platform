# Quick Start — Run the Project (Step by Step)

Complete guide for **Windows**. Adjust paths if your folder name differs.

**Project folder:** `c:\Users\dhanu\OneDrive\Desktop\AI integration`

---

## What you are running

| # | Service | Port | Purpose |
|---|---------|------|---------|
| 1 | **Frontend** (Next.js) | 3000 | Web UI |
| 2 | **Backend** (FastAPI) | 8000 | API + AI processing |
| 3 | **PostgreSQL** | 5432 | Email storage |
| 4 | **Elasticsearch** | 9200 | Keyword search |
| 5 | **ChromaDB** | 8001 | Semantic / similar email search |

---

## Path A — Everything in Docker (easiest)

### Step 0 — Install prerequisites

1. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. Open Docker Desktop and wait until it says **Running**
3. In Docker Desktop → **Settings → Resources**, set **Memory to at least 8 GB**
4. Verify (PowerShell):

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"
.\scripts\verify-prerequisites.ps1
docker --version
docker compose version
```

### Step 1 — One-time Elasticsearch fix (Windows only)

If Elasticsearch fails later, run **PowerShell as Administrator**:

```powershell
wsl -d docker-desktop sysctl -w vm.max_map_count=262144
```

Skip if you are not on Windows/WSL2.

### Step 2 — Create environment file

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"
copy .env.example .env
```

Default values in `.env` work for local use. Do not change unless a port is already taken.

### Step 3 — Build and start all services

```powershell
.\scripts\start.ps1
```

**OR manually:**

```powershell
docker compose up -d --build
```

**First run takes 10–25 minutes** because it:

- Downloads Docker images (~3 GB)
- Installs Python + PyTorch + ML libraries
- Downloads HuggingFace embedding/summary models on first backend start

### Step 4 — Watch startup progress

```powershell
docker compose ps
docker compose logs -f backend
```

Wait until you see:

- `PostgreSQL is ready.`
- `Running Alembic migrations...`
- `Elasticsearch connected`
- `ChromaDB connected`
- `Application startup complete` / Uvicorn running

Press `Ctrl+C` to stop following logs (containers keep running).

### Step 5 — Confirm health

Open in browser or PowerShell:

```powershell
curl http://localhost:8000/api/v1/health
```

Expected: JSON with `"status": "ok"` or `"degraded"` (degraded is OK if ES/Chroma still warming up).

| URL | What |
|-----|------|
| http://localhost:3000 | **Main app** |
| http://localhost:8000/docs | API documentation |
| http://localhost:8000/api/v1/health | Health check |

### Step 6 — Upload test emails

1. Create a ZIP of `.eml` files (see `sample-data/README.md`)
2. Open http://localhost:3000/upload
3. Drag & drop the ZIP
4. Wait until status shows **completed** (page auto-refreshes)

### Step 7 — Use the platform

| Page | URL | Action |
|------|-----|--------|
| Dashboard | http://localhost:3000 | Overview + system health |
| Search | http://localhost:3000/search | Semantic or keyword search |
| Emails | http://localhost:3000/emails | Browse parsed emails |
| Analytics | http://localhost:3000/analytics | Charts and stats |

### Step 8 — Stop the platform

```powershell
.\scripts\stop.ps1
```

**OR:**

```powershell
docker compose down
```

**Reset all data (fresh DB):**

```powershell
docker compose down -v
```

---

## Path B — Local dev (faster UI/backend reload)

Use Docker only for databases; run backend + frontend on your machine.

### Step 1 — Start infrastructure (Docker)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"

docker network create comm_intel_network

docker compose -f docker/docker-compose.postgres.yml up -d
docker compose -f docker/docker-compose.elasticsearch.yml up -d
docker compose -f docker/docker-compose.chroma.yml up -d
```

Wait ~1 minute, then verify:

```powershell
docker ps
```

### Step 2 — Backend setup (Terminal 1)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration\backend"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

copy .env.example .env
```

Run database migrations:

```powershell
.\scripts\setup_database.ps1
```

Initialize search (after ES + Chroma containers are healthy):

```powershell
.\scripts\setup_elasticsearch.ps1
.\scripts\setup_vectors.ps1
```

Start API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Leave this terminal open.

### Step 3 — Frontend setup (Terminal 2)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration\frontend"

npm install

copy .env.example .env.local

npm run dev
```

Open http://localhost:3000

---

## Complete file map (what each part does)

```
AI integration/
├── docker-compose.yml          ← Full stack (Path A)
├── .env.example                ← Root ports / API URL for Docker
├── QUICKSTART.md               ← This file
├── README.md                   ← Full documentation
│
├── docker/
│   ├── docker-compose.postgres.yml
│   ├── docker-compose.elasticsearch.yml
│   ├── docker-compose.chroma.yml
│   └── postgres/init/          ← DB extensions on first start
│
├── backend/
│   ├── Dockerfile              ← API container image
│   ├── .env.example            ← Local backend config
│   ├── .env.docker             ← Config inside Docker network
│   ├── requirements.txt        ← Python dependencies
│   ├── alembic/                ← DB migrations
│   ├── app/
│   │   ├── main.py             ← FastAPI entry
│   │   ├── api/v1/             ← REST routes
│   │   ├── models/             ← PostgreSQL tables
│   │   ├── services/           ← Business logic + AI
│   │   └── repositories/       ← Data access
│   └── scripts/
│       ├── setup_database.ps1
│       ├── setup_elasticsearch.ps1
│       ├── setup_vectors.ps1   ← Chroma HTTP + reindex
│       └── docker-entrypoint.sh
│
├── frontend/
│   ├── Dockerfile              ← Next.js production image
│   ├── .env.example            ← NEXT_PUBLIC_API_URL
│   └── src/app/                ← Pages (upload, search, analytics…)
│
└── scripts/
    ├── start.ps1               ← docker compose up --build
    ├── stop.ps1
    └── verify-prerequisites.ps1
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `docker` not recognized | Install/start Docker Desktop |
| Port 5432/8000/3000 in use | Change ports in `.env` or stop conflicting apps |
| Backend unhealthy 10+ min | Normal on first run (downloading models). Check `docker compose logs backend` |
| Elasticsearch exits | Run `vm.max_map_count` fix (Step 1 Path A); increase Docker RAM |
| Upload works, search empty | Wait for processing to finish; run `docker compose exec backend python scripts/reindex_chroma.py` |
| Frontend "failed to fetch" | Confirm backend at http://localhost:8000/docs; check `NEXT_PUBLIC_API_URL` in `.env` |
| CORS errors | Ensure `CORS_ORIGINS` includes `http://localhost:3000` |

---

## Command cheat sheet

```powershell
# START (full stack)
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"
copy .env.example .env
docker compose up -d --build

# LOGS
docker compose logs -f backend

# STATUS
docker compose ps

# STOP
docker compose down

# FULL RESET
docker compose down -v
```

---

## Checklist before demo

- [ ] Docker Desktop running
- [ ] `docker compose ps` shows 5 services up
- [ ] http://localhost:8000/api/v1/health returns JSON
- [ ] http://localhost:3000 loads
- [ ] ZIP uploaded and status = **completed**
- [ ] Semantic search returns results
- [ ] Analytics page shows charts

You are ready when all boxes are checked.
