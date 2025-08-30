from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from server.router import api_router
from server.broadcast import ws_writer, enqueue
from server.watcher import poll_new_rows_loop
from server.db import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 백그라운드 태스크 시작
    t1 = asyncio.create_task(poll_new_rows_loop(
        db_factory=SessionLocal,
        broadcast=enqueue,
        interval_seconds=5,  # 폴링 주기 (원하면 2~3초로 조정)
    ))
    t2 = asyncio.create_task(ws_writer())
    yield
    # Shutdown: 태스크 종료
    for t in (t1, t2):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Trading Reader (SQLite)",
    lifespan=lifespan,
)

# 개발 편의용 CORS (운영 시 필요한 도메인만 허용 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# 라우터 마운트
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",       # 현재 app 객체 경로
        host="0.0.0.0",
        port=8000,
        reload=True,          # 개발 시만, 운영에선 False 권장
    )