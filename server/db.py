# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# trading.db = app/ 의 한 단계 위
DB_PATH = (Path(__file__).resolve().parents[1] / "trading.db")

# 1) 읽기 전용(권장): 서비스는 조회만 하므로 안전
#    sqlite URI 모드 사용 -> uri=True 필요
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}?mode=ro"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "uri": True,  # ← 쿼리스트링(mode=ro) 사용하려면 필수
    },
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
