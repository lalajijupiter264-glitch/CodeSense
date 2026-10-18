from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings
from app.utils.logger import logger

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import models so they are registered with Base metadata
        import app.database.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully with URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
