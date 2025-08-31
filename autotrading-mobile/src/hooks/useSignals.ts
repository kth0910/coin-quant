// hooks/useSignals.ts
import { useEffect, useRef, useState } from "react";
import { API ,hydrateApiBase } from "@/api/config";
import type { Signal } from "@/types";

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
      // expo-config만 쓰는 경우엔 주석 처리
      await hydrateApiBase();
      console.log("[WS TEST] base:", API.base, "ws:", API.ws);
      await fetchInitial();
      connect();
    })();

    async function fetchInitial() {
      try {
        const r = await fetch(`${API.base}/history?limit=100`);
        const j: Signal[] = await r.json();
        setSignals(j);
      } catch (e) {
        console.warn("fetch history error", e);
      } finally {
        setLoading(false);
      }
    }

    function scheduleReconnect() {
      // 지수 백오프(최대 10초)
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
          if (msg?.event === "history" && msg?.data) {
            setSignals((prev) => [...prev, msg.data].slice(-300));
          }
        } catch {
          // non-JSON은 무시
        }
      };

      wsRef.current.onerror = (err) => {
        console.warn("WebSocket error", err);
        setIsConnected(false);
        try { wsRef.current?.close(); } catch {}
      };

      wsRef.current.onclose = () => {
        console.log("WebSocket closed ❌");
        setIsConnected(false);
        if (ping.current) { clearInterval(ping.current); ping.current = null; }
        scheduleReconnect();
      };
    }

    return () => {
      if (ping.current) clearInterval(ping.current);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      try { wsRef.current?.close(); } catch {}
    };
  }, []);

  // ✅ isConnected 반환에 포함
  return { signals, loading, isConnected };
}
