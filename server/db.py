# server/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# trading.db = project root (server/의 한 단계 위)
DB_PATH = (Path(__file__).resolve().parents[1] / "trading.db")
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}?mode=ro"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},  # sqlite URI 모드
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
