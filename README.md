# hav_scrap — Haveloc Placement Intelligence System

A full-stack desktop-style web application and data extraction platform engineered to extract, normalize, analyze, and synthesize placement drive intelligence from the **Haveloc** college placement portal.

Built with a **FastAPI (Python 3.11+)** backend and a **React 19 + Tailwind CSS** frontend inspired by Tony Stark's JARVIS / Stark Industries telemetry consoles.

---

## 1. System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               REACT 19 FRONTEND HUD                    │
                    │   Tactical Dark Mode • Recharts • Vite • Lucide Icons │
                    └──────────────────────────┬─────────────────────────────┘
                                               │ HTTP / REST / SSE Streaming
                                               ▼
                    ┌────────────────────────────────────────────────────────┐
                    │                FASTAPI BACKEND ENGINE                  │
                    │          Strict 127.0.0.1 Binding • SQLite 3           │
                    ├──────────────────────────┬─────────────────────────────┤
                    │   Core API Subsystems    │   Scraper & Automation      │
                    │   • Portal & Auth Bridge │   • Persistent Browser      │
                    │   • Company Discovery    │   • Multi-tier DOM Parser   │
                    │   • Detailed Extraction  │   • Checkpoint Journaling   │
                    │   • Normalization Engine │   • Task Manager & SSE Hub  │
                    │   • OpenPyXL Exporter    │   • Rate-limit Delays       │
                    │   • Multi-dim Analytics  │   • Human-in-the-Loop Login │
                    └──────────────────────────┴─────────────────────────────┘
                                               │
                    ┌──────────────────────────┴─────────────────────────────┐
                    │                   PERSISTENT STORAGE                   │
                    │  • SQLite: data/hav_scrap.db                           │
                    │  • Browser Profile: data/browser_profile/              │
                    │  • Database Backups: data/backups/                     │
                    │  • Excel Deliverables: data/exports/                   │
                    │  • Rotating Logs: logs/hav_scrap.log                   │
                    └────────────────────────────────────────────────────────┘
```

---

## 2. Key Features

* **Authenticated Persistent Session:** Headed Chromium browser context preserves session cookies and tokens in `data/browser_profile/`.
* **Human-in-the-Loop Authentication:** Manual login workflow preserves portal security—never automates CAPTCHA or stores passwords.
* **Resilient Scraper Engine:** Background task manager with real-time Server-Sent Events (SSE) streaming, non-destructive pause/resume checkpoints, and window closure auto-detection.
* **Data Cleaning & Salary Normalization:** Strips HTML noise, categorizes compensation packages (`FIXED_CTC`, `CTC_RANGE`, `FIXED_PLUS_VARIABLE`, `MONTHLY_SALARY`, `INTERNSHIP_STIPEND`), and isolates internship stipends from full-time CTC.
* **Audit & Data Quality Scoring:** Continuous audit metrics tracking valid records, operator review queues, and potential duplicates.
* **6-Worksheet Excel Deliverables:** Custom OpenPyXL engine generating multi-sheet `.xlsx` files with formula injection protection (`CWE-1236`), dark navy headers, auto-filters, frozen panes, and responsive column widths:
  1. `All Companies`
  2. `All Job Opportunities`
  3. `Salary Comparison` (sorted descending by normalized LPA)
  4. `Internship Opportunities` (strict stipend isolation)
  5. `Eligibility Details` (CGPA, branches, backlogs, batch)
  6. `Data Quality Report` (executive audit dashboard)
* **Multi-Dimensional Analytics:** Company rankings, 7-bracket LPA distribution histogram, hiring hub geographic density, and academic eligibility requirements.
* **Atomic Database Backups:** Online non-destructive SQLite snapshot backups with automated `PRAGMA integrity_check` verification saved to `data/backups/`.

---

## 3. Technology Stack

* **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.x, SQLite, Pydantic v2, Playwright, BeautifulSoup4, OpenPyXL.
* **Frontend:** React 19, Vite, Tailwind CSS, Lucide React, Recharts, Axios, React Router DOM.
* **Storage:** Local SQLite database (`data/hav_scrap.db`) and filesystem archives.

---

## 4. Directory Structure

```
Haveloc_Placement_Scraper/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST route handlers (companies, jobs, scraper, analytics, exports, system)
│   │   ├── core/                # Configuration, security settings, rotating logging
│   │   ├── database/            # SQLAlchemy session, migrations, and atomic backup engine
│   │   ├── exporters/           # OpenPyXL 6-sheet workbook synthesizer & formula sanitization
│   │   ├── models/              # SQLAlchemy models (Company, JobOpportunity, ScrapingSession, ExportHistory)
│   │   ├── processors/          # Cleaners, salary converters, normalizers, deduplicators, validators
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── scraper/             # Browser manager, auth manager, task runner, SSE event manager
│   │   ├── services/            # Business services coordinating database and scraper logic
│   │   └── main.py              # Application lifespan, CORS, error handling
│   ├── requirements.txt         # Pinned backend dependencies
│   └── venv/                    # Isolated Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/          # StatCards, ChartCards, SectionHeaders, StatusBadges
│   │   ├── pages/               # Dashboard, ScraperControl, Companies, SalaryIntelligence, Analytics, ExportCenter, Settings
│   │   └── services/api.js      # Centralized Axios API service with response telemetry
│   ├── package.json             # Frontend dependencies
│   └── tailwind.config.js       # JARVIS palette configuration
├── data/
│   ├── hav_scrap.db             # Primary SQLite production database
│   ├── backups/                 # Verified timestamped SQLite backups
│   ├── browser_profile/         # Persistent Chromium user profile (cookies/session)
│   └── exports/                 # Generated Excel deliverables (.xlsx)
├── logs/
│   └── hav_scrap.log            # Rotating application audit logs (10 MB, 5 backups)
├── start_hav_scrap.bat          # 1-click Windows production startup script
├── stop_hav_scrap.bat           # Safe shutdown script (kills only ports 8000 & 5173)
├── .env.example                 # Environment variable template
├── .gitignore                   # Security exclusion rules
└── README.md                    # System documentation
```

---

## 5. Quick Start Instructions

### Prerequisites
* Windows 10/11
* Python 3.11+
* Node.js v18+ and npm

### Installation

1. **Clone or navigate to workspace:**
   ```bash
   cd D:\Study_material\python_mark1\project\Haveloc_Placement_Scraper
   ```

2. **Set up Backend Environment:**
   ```bash
   python -m venv backend\venv
   backend\venv\Scripts\pip install -r backend\requirements.txt
   ```

3. **Install Frontend Dependencies:**
   ```bash
   npm --prefix frontend install
   ```

4. **Install Playwright Chromium Browser:**
   ```bash
   backend\venv\Scripts\playwright install chromium
   ```

---

## 6. Starting & Stopping the Application

### Launch
Double-click `start_hav_scrap.bat` or run:
```cmd
start_hav_scrap.bat
```
This script validates your virtual environment, checks port availability, starts the FastAPI backend, launches the Vite frontend, and displays access URLs:
* **Frontend Console:** `http://localhost:5173`
* **FastAPI Backend:** `http://127.0.0.1:8000`
* **Interactive API Docs:** `http://127.0.0.1:8000/api/docs`

### Safe Shutdown
Double-click `stop_hav_scrap.bat` or run:
```cmd
stop_hav_scrap.bat
```
This terminates only the processes listening on ports `8000` and `5173`. Unrelated Python and Node processes are left untouched.

---

## 7. Haveloc Portal Authentication Workflow

1. Navigate to **Portal Connection** or **Scraper Control** on `http://localhost:5173`.
2. Click **Connect Portal** to launch a headed Chromium browser window.
3. Log in manually with your Haveloc college placement portal credentials and complete any multi-factor challenge.
4. Once logged in and on the eligible jobs dashboard, the system detects successful authentication and marks the connection as **AUTHENTICATED**.
5. Session state is persisted in `data/browser_profile/` and reused across sessions.
6. **Security Guarantee:** Portal passwords, authentication tokens, and cookies are never logged or stored in plain text.

---

## 8. Database Management & Backups

* **Location:** `data/hav_scrap.db`
* **Backups:** Created using SQLite online snapshot threading and verified with `PRAGMA integrity_check`.
* **Triggering a Backup:**
  * Through the **Settings** page in the UI: Click **CREATE ATOMIC DATABASE BACKUP**.
  * Through the API: `POST /api/system/backup`
* Backup files are saved with timestamped filenames (`hav_scrap_backup_YYYY-MM-DD_HHMMSS.db`) inside `data/backups/`. Existing backups are never overwritten or deleted.

---

## 9. Security & Hardening Controls

* **Local Binding:** The backend binds strictly to `127.0.0.1:8000`. Public external binding is disabled by default.
* **CORS Restrictions:** Only requests from `http://localhost:5173` and `http://127.0.0.1:5173` are permitted.
* **Directory Traversal Immunity (CWE-22):** All export download and deletion routes validate that target paths reside strictly inside `data/exports/`.
* **Sensitive Data Scrubbing (CWE-532):** The rotating file logger intercepts records and redacts passwords, bearer tokens, cookies, and authorization headers.
* **Formula Injection Shielding (CWE-1236):** Export cells with leading characters (`=`, `+`, `-`, `@`) are prepended with an apostrophe (`'`) to prevent spreadsheet calculation exploits.
* **Git Exclusions:** Credentials, `data/browser_profile/`, databases, backups, and logs are excluded in `.gitignore`.

---

## 10. API Reference Overview

| Route | Method | Subsystem | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Health | Health probe and uptime status |
| `/api/system/status` | `GET` | System | Core engine telemetry and database connectivity |
| `/api/system/backup` | `POST` | System | Triggers an atomic, verified SQLite database backup |
| `/api/system/backups` | `GET` | System | Lists verified database backups in `data/backups/` |
| `/api/portal/status` | `GET` | Portal | Checks Chromium connection and session validity |
| `/api/portal/connect` | `POST` | Portal | Launches persistent Chromium context for manual login |
| `/api/discovery/start` | `POST` | Discovery | Starts multi-page recruiter and listing extraction |
| `/api/extraction/details/start` | `POST` | Extraction | Extracts detailed job roles, criteria, and CTC |
| `/api/processing/start` | `POST` | Normalization | Runs data cleaning, validation, and salary normalization |
| `/api/exports/generate` | `POST` | Exports | Synthesizes 6-sheet OpenPyXL Excel deliverable |
| `/api/exports/{id}/download` | `GET` | Exports | Streams validated `.xlsx` workbook to client |
| `/api/analytics/overview` | `GET` | Analytics | Computes placement KPIs, averages, and median CTC |
| `/api/analytics/company-rankings`| `GET` | Analytics | Returns recruiter league table sorted by CTC or volume |
| `/api/analytics/salary-distribution`| `GET` | Analytics | Returns 7-tier LPA frequency histogram |
| `/api/analytics/salary-intelligence`| `GET` | Analytics | Detailed compensation records with search and pagination |

---

## 11. Troubleshooting

* **Backend port 8000 already in use:** Run `stop_hav_scrap.bat` to release the port, then rerun `start_hav_scrap.bat`.
* **Playwright browser fails to launch:** Run `backend\venv\Scripts\playwright install chromium` inside the project root.
* **Portal session expired:** In the frontend, navigate to **Portal Connection**, click **Disconnect**, then click **Connect Portal** to refresh your session.
* **Corrupted or locked database:** Check `data/backups/` for the latest verified snapshot. SQLite uses WAL mode with automatic timeout handling.



.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 
npm run dev
RA2311003010190-01011970