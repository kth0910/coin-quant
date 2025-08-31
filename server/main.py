# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from router import api_router
from broadcast import ws_writer, enqueue  # enqueue는 외부에서 사용
from watcher import poll_new_rows_loop
from db import SessionLocal
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 백그라운드 태스크 시작
    t_poll = asyncio.create_task(
        poll_new_rows_loop(
            db_factory=SessionLocal,
            broadcast=enqueue,     # ← 큐에 적재
            interval_seconds=5,
        )
    )
    t_writer = asyncio.create_task(ws_writer())  # ← 큐 소비 & 송신
    yield
    # 종료
    for t in (t_poll, t_writer):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Trading Reader (SQLite)", lifespan=lifespan)

# 개발용 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
