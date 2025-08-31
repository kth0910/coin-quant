// hooks/useSignals.ts
import { useEffect, useRef, useState, useMemo } from "react";
import { API, hydrateApiBase } from "@/api/config";
import type { Signal as RawSignal } from "@/types";

// 서버 응답 래퍼 타입
type HistoryResponse = {
  items: RawSignal[];
  next_cursor?: string | null;
};

// 허용 enum
const ALLOWED_TYPES = new Set(["BUY", "SELL", "HOLD", "ALERT"] as const);
type AllowedType = "BUY" | "SELL" | "HOLD" | "ALERT";

// 타입 가드/헬퍼
function isHistoryResponse(x: any): x is HistoryResponse {
  return x && typeof x === "object" && Array.isArray(x.items);
}
function isSignalArray(x: any): x is RawSignal[] {
  return Array.isArray(x) && (x.length === 0 || (x[0] && "ts" in x[0]));
}

// 정규화: 서버에서 오는 임의 값들을 안전한 Signal로 변환
function normalizeSignal(s: any): RawSignal {
  console.log("raw 값 : ", s)
  const id = Number.isFinite(+s?.id) ? Number(s.id) : -1;
  const ts = typeof s?.ts === "string" ? s.ts : new Date().toISOString();
  const ticker = typeof s?.ticker === "string" ? s.ticker : "BTC/KRW";
  const priceNum = Number(s?.price);
  const confidenceNum = Number(s?.confidence);

  let typ = String(s?.type ?? "HOLD").toUpperCase();
  if (!ALLOWED_TYPES.has(typ as AllowedType)) typ = "HOLD";

  return {
    id,
    ts,
    ticker,
    price: Number.isFinite(priceNum) ? priceNum : 0,
    type: typ as AllowedType,
    confidence: Number.isFinite(confidenceNum) ? confidenceNum : 0,
    reason: typeof s?.reason === "string" ? s.reason : undefined,
  };
}

// 정렬/중복 제거
function sortByTsAsc(list: RawSignal[]) {
  return [...list].sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
  );
}
function dedupById(list: RawSignal[]) {
  const seen = new Set<number>();
  const out: RawSignal[] = [];
  for (const s of list) {
    if (typeof s.id === "number" && seen.has(s.id)) continue;
    if (typeof s.id === "number") seen.add(s.id);
    out.push(s);
  }
  return out;
}

export function useSignals() {
  const [signals, setSignals] = useState<RawSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const ping = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryRef = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    (async () => {
      await hydrateApiBase();
      console.log("[WS TEST] base:", API.base, "ws:", API.ws);
      await fetchInitial();
      connect();
    })();

    async function fetchInitial() {
      try {
        const r = await fetch(`${API.base}/history?limit=100`);
        const j = await r.json();

        let arr: RawSignal[] = [];
        if (isSignalArray(j)) {
          arr = j.map(normalizeSignal);
        } else if (isHistoryResponse(j)) {
          arr = (j.items ?? []).map(normalizeSignal);
        } else {
          console.warn("Unknown /history shape:", j);
        }

        setSignals(dedupById(sortByTsAsc(arr)));
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

          // 초기 배열 (bootstrap/history 이벤트)
          if (
            (msg?.event === "bootstrap" || msg?.event === "history") &&
            Array.isArray(msg?.data)
          ) {
            const arr = msg.data.map(normalizeSignal);
            setSignals((_) => dedupById(sortByTsAsc(arr)));
            setLoading(false);
            return;
          }

          // 신규 단건
          if (msg?.event === "signal" && msg?.data) {
            const one = normalizeSignal(msg.data);
            setSignals((prev) => dedupById(sortByTsAsc([...prev, one])));
            return;
          }

          if (msg?.event === "pong") return;
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
