// charts/CandleLike.tsx
import React, { useMemo } from "react";
import { View, Text } from "react-native";
import { CartesianChart, Line, Bar } from "victory-native";

type Raw = { x?: any; open?: any; high?: any; low?: any; close?: any };
type Point = { x: number; open: number; high: number; low: number; close: number };

const num = (v: any) => {
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? n : NaN;
};

export default function CandleLike({ data }: { data: Raw[] }) {
  // 1) 숫자로 강제 변환 + 불량 데이터 필터
  const clean: Point[] = useMemo(() => {
    const arr = (data ?? []).map((d, i) => ({
      x: Number.isFinite(num(d.x)) ? num(d.x) : i, // x 없으면 인덱스 사용
      open: num(d.open),
      high: num(d.high),
      low: num(d.low),
      close: num(d.close),
    }));
    const filtered = arr.filter(
      (d) =>
        Number.isFinite(d.x) &&
        Number.isFinite(d.open) &&
        Number.isFinite(d.high) &&
        Number.isFinite(d.low) &&
        Number.isFinite(d.close)
    );
    if (filtered.length !== arr.length) {
      const badAt = arr.findIndex(
        (d) =>
          !Number.isFinite(d.x) ||
          !Number.isFinite(d.open) ||
          !Number.isFinite(d.high) ||
          !Number.isFinite(d.low) ||
          !Number.isFinite(d.close)
      );
      console.warn("CandleLike: dropped invalid point at index", badAt, arr[badAt]);
    }
    return filtered;
  }, [data]);

  if (!clean.length) {
    return (
      <View style={{ padding: 12 }}>
        <Text style={{ color: "orange" }}>No valid data for chart.</Text>
      </View>
    );
  }

  // 2) 도형용 데이터 구성
  const wickHigh = clean.map((d) => ({ x: d.x, y: d.high }));
  const wickLow = clean.map((d) => ({ x: d.x, y: d.low }));
  const bodyTop = clean.map((d) => ({ x: d.x, y: Math.max(d.open, d.close) }));
  const bodyBot = clean.map((d) => ({ x: d.x, y: Math.min(d.open, d.close) }));

  // 3) barWidth 안전 계산
  const barWidth = Math.max(2, Math.floor((300 / Math.max(1, clean.length)) * 0.6));

  return (
    <CartesianChart
      data={clean}
      xKey="x"
      yKeys={["high", "low"]} // 스케일 산정용
      domainPadding={{ left: 24, right: 24, top: 12, bottom: 20 }}
      style={{ height: 220 }}
      axisOptions={{ tickCount: 4 }}
    >
      {/* 수염: high/low 선 */}
      <Line points={wickHigh} strokeWidth={1} />
      <Line points={wickLow} strokeWidth={1} />
      {/* 바디: y(아래) ~ y2(위) 막대 */}
      {bodyTop.map((top, i) => {
        const bot = bodyBot[i];
        if (!Number.isFinite(top.y) || !Number.isFinite(bot.y)) return null;
        return (
          <Bar
            key={i}
            x={top.x}
            y={bot.y}
            y2={top.y}
            barWidth={barWidth}
          />
        );
      })}
    </CartesianChart>
  );
}
