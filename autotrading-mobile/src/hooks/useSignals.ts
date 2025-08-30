import { useEffect, useRef, useState } from "react";
import { API, hydrateApiBase } from "@/api/config";
import type { Signal } from "@/types";

export function useSignals() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const ping = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    (async () => {
      await hydrateApiBase();
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

    function connect() {
      wsRef.current = new WebSocket(API.ws);
      wsRef.current.onopen = () => {
        ping.current = setInterval(() => wsRef.current?.send("ping"), 15000);
      };
      wsRef.current.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.event === "history") {
            setSignals(prev => [...prev, msg.data].slice(-300));
          }
        } catch {}
      };
      wsRef.current.onclose = () => {
        clearInterval(ping.current!);
        setTimeout(connect, 2000);
      };
      wsRef.current.onerror = () => wsRef.current?.close();
    }

    return () => { clearInterval(ping.current!); wsRef.current?.close(); };
  }, []);

  return { signals, loading };
}
