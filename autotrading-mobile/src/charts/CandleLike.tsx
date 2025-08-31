// src/charts/CandleLike.tsx
import React from "react";
import { View } from "react-native";

// ✅ ESM/CJS 환경 차이 안전 우회
import * as Vraw from "victory-native";
const V: any = (Vraw as any).default ?? Vraw;

// ✅ 테마는 core victory에서
import { VictoryTheme } from "victory";

type Point = { ts: string; price: number; type?: "BUY" | "SELL" | "HOLD" };

export default function CandleLike({ data }: { data: Point[] }) {
  // 차트는 index 기반 x축으로 간단화
  const line = data.map((d, i) => ({ x: i + 1, y: d.price }));
  const buys  = data
    .map((d, i) => (d.type === "BUY"  ? { x: i + 1, y: d.price } : null))
    .filter(Boolean) as { x: number; y: number }[];
  const sells = data
    .map((d, i) => (d.type === "SELL" ? { x: i + 1, y: d.price } : null))
    .filter(Boolean) as { x: number; y: number }[];

  return (
    <View>
      <V.VictoryChart theme={VictoryTheme.material} domainPadding={{ x: 16, y: 10 }}>
        <V.VictoryAxis tickCount={6} />
        <V.VictoryAxis dependentAxis tickCount={5} />
        <V.VictoryLine data={line} />

        {/* BUY / SELL 마커 (선택) */}
        {buys.length > 0 && (
          <V.VictoryScatter data={buys} size={3} />
        )}
        {sells.length > 0 && (
          <V.VictoryScatter data={sells} size={3} />
        )}
      </V.VictoryChart>
    </View>
  );
}
