import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env
load_dotenv()

from app.webhooks.whatsapp import router as whatsapp_router
from app.webhooks.telegram import router as telegram_router
from app.webhooks.calendly import router as calendly_router
from app.routers.leads import router as leads_router
from app.routers.inventory import router as inventory_router
from app.routers.health import router as health_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager
from app.cache.redis import close_redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis_client()

app = FastAPI(
    title="Reva API",
    description="Reva — AI sales engine for Nigerian real estate developers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — tighten in production by setting ALLOWED_ORIGINS env var
# ---------------------------------------------------------------------------
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(whatsapp_router, prefix="/webhook")
app.include_router(telegram_router, prefix="/webhook")
app.include_router(calendly_router, prefix="/webhook")
app.include_router(leads_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(health_router, prefix="/api")

# ---------------------------------------------------------------------------
# Static files + Dashboard
# ---------------------------------------------------------------------------
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return {"message": "Reva API is running. Visit /docs for the API reference."}


@app.get("/dashboard", tags=["Dashboard"], summary="Live lead pipeline dashboard")
async def dashboard():
    dashboard_file = STATIC_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(str(dashboard_file))
    return {"message": "Dashboard file not found."}
