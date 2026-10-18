from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import init_db
from app.utils.logger import logger
from app.api.routes_health import router as health_router
from app.api.routes_analyze import router as analyze_router
from app.api.routes_history import router as history_router
from app.api.routes_insights import router as insights_router


# Initialize DB tables on application module load
try:
    init_db()
except Exception as e:
    logger.warning(f"Initial DB creation notice: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    logger.info(f"Starting {settings.app_name} on environment '{settings.environment}'...")
    try:
        init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.app_name}...")


TAGS_METADATA = [
    {
        "name": "Health",
        "description": "System operational status, OpenJDK compiler availability, database connectivity, and AI key status.",
    },
    {
        "name": "Analysis",
        "description": "Full compiler execution pipeline, deterministic taxonomy classification, static heuristics, and validated code corrections.",
    },
    {
        "name": "History",
        "description": "Submission history timeline and historical detailed retrospective inspection.",
    },
    {
        "name": "Insights",
        "description": "Personalized analytics, error taxonomy frequency breakdown, and curated learning recommendations.",
    },
]

app = FastAPI(
    title="CodeSense API",
    description="Intelligent Compiler Error Analyzer, Diagnostic Taxonomy Classifier, and Validated Fix Engine API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://codesense.vercel.app",
]
if settings.frontend_url:
    cleaned = settings.frontend_url.strip().rstrip("/")
    if cleaned and cleaned not in origins:
        origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Permits all Vercel preview & production branches
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Clean global exception handler to avoid exposing raw internal stack traces."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please check server logs."
            }
        }
    )


# Include API Routers
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(insights_router)


@app.get("/api/docs", include_in_schema=False)
def api_docs_redirect():
    """Support direct /api/docs endpoint pointing to interactive Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/", summary="API Root", description="Returns welcome message and links to interactive documentation.")
def root():
    return {
        "message": "Welcome to CodeSense API — Intelligent Compiler Error Analyzer",
        "docs": "/docs",
        "api_docs": "/api/docs",
        "health": "/api/health"
    }
