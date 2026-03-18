"""
System entry point.

Initialises the FastAPI application, mounts static files, configures the
Jinja2 template engine, registers all feature routers, and creates the
database tables on startup.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.database import create_db_and_tables

# ── Feature routers ──────────────────────────────────────────────────────────
from src.features.manage_employees.router import router as employees_router
from src.features.manage_companies.router import router as companies_router
from src.features.manage_projects.router import router as projects_router
from src.features.manage_quotes.router import router as quotes_router
from src.features.manage_tasks.router import router as tasks_router
from src.features.submit_timesheet.router import router as timesheet_router
from src.features.analyze_burn_rate.router import router as burn_rate_router

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    create_db_and_tables()
    yield


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Project LINKER Turbo",
    description="Workforce & project management platform — MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ── Templates (shared Jinja2 instance exposed for routers that need it) ───────
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(employees_router, prefix="/employees", tags=["Employees"])
app.include_router(companies_router, prefix="/companies", tags=["Companies"])
app.include_router(projects_router,  prefix="/projects",  tags=["Projects"])
app.include_router(quotes_router,    prefix="/quotes",    tags=["Quotes"])
app.include_router(tasks_router,     prefix="/tasks",     tags=["Tasks"])
app.include_router(timesheet_router, prefix="/timesheet", tags=["Timesheet"])
app.include_router(burn_rate_router, prefix="/burn-rate", tags=["Burn Rate"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "Project LINKER Turbo"}
