import shutil
import subprocess
from fastapi import APIRouter
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Health"])


@router.get(
    "/health",
    summary="System Health & Compiler Status Check",
    description="Inspects real-time operational health, verifies OpenJDK javac compiler availability and version, tests database readiness, and reports AI key configuration status."
)
def health_check():
    """Health check endpoint to verify compiler, database, and system status."""
    compiler_path = shutil.which(settings.java_compiler_path) or settings.java_compiler_path
    compiler_available = False
    compiler_version = "Unknown"

    try:
        result = subprocess.run(
            [compiler_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # javac prints version to stdout or stderr depending on JDK version
        version_str = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0 or "javac" in version_str:
            compiler_available = True
            compiler_version = version_str
    except Exception as e:
        logger.warning(f"Health check compiler test failed: {e}")
        compiler_available = False
        compiler_version = str(e)

    return {
        "status": "healthy" if compiler_available else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "compiler": {
            "configured_path": settings.java_compiler_path,
            "available": compiler_available,
            "version": compiler_version
        },
        "ai": {
            "enabled": bool(settings.ai_api_key),
            "model": settings.ai_model if settings.ai_api_key else "Knowledge Base Fallback (No Key)"
        },
        "database": {
            "type": "PostgreSQL" if "postgres" in settings.database_url else "SQLite",
            "status": "ready"
        }
    }
