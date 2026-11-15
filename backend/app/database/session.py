import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.db_models import Base

os.makedirs("data", exist_ok=True)

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

def init_db():
    Base.metadata.create_all(bind=sync_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
