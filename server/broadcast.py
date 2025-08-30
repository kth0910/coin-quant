import asyncio
from typing import Dict, Any, List
from fastapi import WebSocket

# 구독자(웹소켓) 목록과 메시지 큐
subscribers: set[WebSocket] = set()
msg_queue: List[Dict[str, Any]] = []

def enqueue(payload: Dict[str, Any]) -> None:
    """watcher에서 호출: 메시지를 큐에 쌓는다."""
    msg_queue.append(payload)

async def ws_writer():
    """큐에 쌓인 payload를 모든 구독자에게 전송"""
    while True:
        try:
            if msg_queue and subscribers:
                payload = msg_queue.pop(0)
                dead = []
                for ws in list(subscribers):
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    subscribers.discard(ws)
        except Exception:
            # 필요 시 로깅
            pass
        await asyncio.sleep(0.05)
