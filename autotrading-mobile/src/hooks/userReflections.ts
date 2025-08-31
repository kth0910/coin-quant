// hooks/useReflections.ts
import { useEffect, useRef, useState } from "react";
import { API, hydrateApiBase } from "@/api/config";

export type Reflection = {
  id: number;
  trading_id: number;
  reflection_date: string; // ISO
  market_condition: string;
  decision_analysis: string;
  improvement_points: string;
  success_rate: number;
  learning_points: string;
};

type ReflectionsResponse = {
  items: Reflection[];
  next_cursor?: string | null;
};

function isReflectionsResponse(x: any): x is ReflectionsResponse {
  return x && typeof x === "object" && Array.isArray(x.items);
}

export function useReflections() {
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [loading, setLoading] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    (async () => {
      await hydrateApiBase();
      await fetchInitial();
      connect();
    })();

    async function fetchInitial() {
      try {
        const r = await fetch(`${API.base}/reflections?limit=120`);
        const j = await r.json();
        if (isReflectionsResponse(j)) {
          setReflections(j.items);
        } else if (Array.isArray(j)) {
          setReflections(j);
        } else {
          console.warn("Unknown /reflections shape:", j);
        }
      } catch (e) {
        console.warn("fetch reflections error", e);
      } finally {
        setLoading(false);
      }
    }

    function connect() {
      try { wsRef.current?.close(); } catch {}
      wsRef.current = new WebSocket(API.ws);

      wsRef.current.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);

          if (msg?.event === "bootstrap_reflections" && Array.isArray(msg?.data)) {
            setReflections(msg.data);
            return;
          }
          if (msg?.event === "reflection" && msg?.data) {
            setReflections((prev) => [...prev, msg.data]);
            return;
          }
        } catch (e) {
          console.warn("WS parse error(reflection):", e);
        }
      };
    }

    return () => { try { wsRef.current?.close(); } catch {} };
  }, []);

  return { reflections, loading };
}
