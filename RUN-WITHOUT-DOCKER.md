# Run Without Docker (Windows)

Use this guide when you see:

```text
Docker Desktop is unable to start
```

Your machine has **Python** and **Node** but **WSL is not installed**, which Docker Desktop needs on Windows.

---

## Choose one path

| Path | When to use |
|------|-------------|
| **A — Fix Docker** | You want the full stack in containers |
| **B — No Docker** | Run backend + frontend locally (recommended for you now) |

---

# Path A — Fix Docker Desktop

### 1. Install WSL2 (required)

Open **PowerShell as Administrator**:

```powershell
wsl --install
```

Restart your PC when prompted.

After restart:

```powershell
wsl --set-default-version 2
wsl --status
```

### 2. Enable virtualization (if still failing)

- Reboot → enter BIOS/UEFI
- Enable **Intel VT-x** or **AMD-V** (virtualization)
- In Windows: **Settings → Apps → Optional features** → enable **Virtual Machine Platform** and **Windows Subsystem for Linux**

### 3. Start Docker Desktop

- Open **Docker Desktop** from Start menu
- Wait until the whale icon shows **Running**
- Then:

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"
docker compose up -d --build
```

---

# Path B — No Docker (local run)

You need **PostgreSQL** installed on Windows. Elasticsearch is **optional** (keyword search only).

### Step 1 — Install PostgreSQL

**Option 1 — winget (Admin PowerShell):**

```powershell
winget install PostgreSQL.PostgreSQL.16
```

During setup, note the password you set for user `postgres`.

**Option 2 — Installer:** https://www.postgresql.org/download/windows/

### Step 2 — Create database and user

Open **SQL Shell (psql)** or pgAdmin and run:

```sql
CREATE USER comm_intel WITH PASSWORD 'comm_intel_secret';
CREATE DATABASE comm_intel_db OWNER comm_intel;
GRANT ALL PRIVILEGES ON DATABASE comm_intel_db TO comm_intel;
```

Or match passwords in `backend\.env` if you use different values.

### Step 3 — Backend setup

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration\backend"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

copy .env.example .env
```

Edit `backend\.env` — minimum for no-Docker:

```env
DEBUG=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=comm_intel
POSTGRES_PASSWORD=comm_intel_secret
POSTGRES_DB=comm_intel_db

# Chroma: local folder, no Docker server
CHROMA_MODE=persistent
CHROMA_ENABLED=true

# Elasticsearch OFF until you install it or fix Docker
ELASTICSEARCH_ENABLED=false
```

Run migrations:

```powershell
alembic upgrade head
```

Start API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Leave this terminal open. First start downloads ML models (5–15 min).

### Step 4 — Frontend (new terminal)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration\frontend"

npm install
copy .env.example .env.local

npm run dev
```

### Step 5 — Open the app

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Web UI |
| http://localhost:8000/docs | API |
| http://localhost:8000/api/v1/health | Health |

### What works without Elasticsearch

| Feature | Works? |
|---------|--------|
| Upload ZIP / parse emails | Yes |
| PostgreSQL storage | Yes |
| AI summaries | Yes (after model download) |
| Semantic search (Chroma local) | Yes |
| Similar emails | Yes |
| Analytics dashboard | Yes |
| Keyword search | No (needs Elasticsearch) |

---

## Quick start script (no Docker)

```powershell
cd "c:\Users\dhanu\OneDrive\Desktop\AI integration"
.\scripts\run-local.ps1
```

See `scripts\run-local.ps1` for details.
