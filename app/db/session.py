from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, autocommit=False, autoflush=False)


def get_db():
    """Provide one database session per request and always release its connection."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
