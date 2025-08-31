// hooks/useSignals.ts
import { useEffect, useRef, useState } from "react";
import { API, hydrateApiBase } from "@/api/config";
import type { Signal } from "@/types";

type HistoryResponse = {
  items: Signal[];
  next_cursor?: string | null;
};

// 타입 가드
function isHistoryResponse(x: any): x is HistoryResponse {
  return x && typeof x === "object" && Array.isArray(x.items);
}
function isSignalArray(x: any): x is Signal[] {
  return Array.isArray(x) && (x.length === 0 || ("id" in x[0] && "ts" in x[0]));
}

// 정렬 유틸 (ts 오름차순)
function sortByTsAsc(list: Signal[]) {
  return [...list].sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
  );
}

export function useSignals() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const ping = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryRef = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    (async () => {
      await hydrateApiBase(); // (환경변수/설정 주입용)
      console.log("[WS TEST] base:", API.base, "ws:", API.ws);
      await fetchInitial();
      connect();
    })();

    async function fetchInitial() {
      try {
        const r = await fetch(`${API.base}/history?limit=100`);
        const j = await r.json();

        if (isSignalArray(j)) {
          // 서버가 배열을 직접 반환하는 경우(구버전/커스텀)
          setSignals(sortByTsAsc(j));
        } else if (isHistoryResponse(j)) {
          // 현재 서버 표준: { items, next_cursor }
          setSignals(sortByTsAsc(j.items));
        } else {
          console.warn("Unknown /history shape:", j);
        }
      } catch (e) {
        console.warn("fetch history error", e);
      } finally {
        setLoading(false);
      }
    }

    function scheduleReconnect() {
      const delay = Math.min(10000, 1000 * 2 ** Math.min(retryRef.current, 3));
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      reconnectTimer.current = setTimeout(connect, delay);
      retryRef.current += 1;
    }

    function connect() {
      try {
        wsRef.current?.close();
      } catch {}
      wsRef.current = new WebSocket(API.ws);

      wsRef.current.onopen = () => {
        console.log("WebSocket connected ✅");
        setIsConnected(true);
        retryRef.current = 0;
        if (ping.current) clearInterval(ping.current);
        ping.current = setInterval(() => wsRef.current?.send("ping"), 15000);
      };

      wsRef.current.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);

          // 서버가 "bootstrap" 또는 "history" 이벤트로 초기 배열을 보냄
          if (
            (msg?.event === "bootstrap" || msg?.event === "history") &&
            Array.isArray(msg?.data)
          ) {
            // 안전하게 정렬
            setSignals(sortByTsAsc(msg.data));
            setLoading(false);
            return;
          }

          // 신규 단건 시그널
          if (msg?.event === "signal" && msg?.data) {
            setSignals((prev) => sortByTsAsc([...prev, msg.data]));
            return;
          }

          if (msg?.event === "pong") {
            return;
          }
        } catch (e) {
          console.warn("WS parse error:", e);
        }
      };

      wsRef.current.onerror = (err) => {
        console.warn("WebSocket error", err);
        setIsConnected(false);
        try {
          wsRef.current?.close();
        } catch {}
      };

      wsRef.current.onclose = () => {
        console.log("WebSocket closed ❌");
        setIsConnected(false);
        if (ping.current) {
          clearInterval(ping.current);
          ping.current = null;
        }
        scheduleReconnect();
      };
    }

    return () => {
      if (ping.current) clearInterval(ping.current);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      try {
        wsRef.current?.close();
      } catch {}
    };
  }, []);

  return { signals, loading, isConnected };
}
