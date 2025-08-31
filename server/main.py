# server/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio, uvicorn

from router import api_router
from broadcast import ws_writer, enqueue
from watcher import poll_new_rows_loop
from db import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[lifespan] starting tasks…")
    writer_task = asyncio.create_task(ws_writer())
    poll_task = asyncio.create_task(
        poll_new_rows_loop(SessionLocal, enqueue, interval_seconds=3, start_from_latest=True, bootstrap_last=120)
    )
    try:
        yield
    finally:
        print("[lifespan] shutting down…")
        for t in [poll_task, writer_task]:
            t.cancel()
        await asyncio.gather(*[writer_task, poll_task], return_exceptions=True)

app = FastAPI(lifespan=lifespan)

# 개발용 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 배포 시 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    # 백그라운드 실행 예:  nohup python -m server.main > server.log 2>&1 &
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
