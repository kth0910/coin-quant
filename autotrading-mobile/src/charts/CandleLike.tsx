// src/charts/CandleLike.tsx
import React, { useMemo } from "react";
import { View } from "react-native";
import { CartesianChart, useChartPressState } from "victory-native"; // Cartesian 컨테이너만 사용
import { Circle, Path, Skia } from "@shopify/react-native-skia";

type Point = { ts: string; price: number; type?: "BUY" | "SELL" | "HOLD" };

export default function CandleLike({ data }: { data: Point[] }) {
  // 1) Hook 순서 고정
  const { state } = useChartPressState({ x: 0, y: { price: 0 } });

  // 2) 데이터 전처리 (x: index, y: price)
  const pts = useMemo(
    () =>
      (data ?? []).map((d, i) => ({
        x: i + 1,
        y: Number(d.price ?? 0),
        type: d.type,
      })),
    [data]
  );

  const buys = useMemo(() => pts.filter((p) => p.type === "BUY"), [pts]);
  const sells = useMemo(() => pts.filter((p) => p.type === "SELL"), [pts]);

  // 3) 축 옵션 (폰트는 전달하지 않음: 기본 폰트 사용 → font.getSize 에러 회피)
  const axisOptions = { lineWidth: 1 } as const;

  
  return (
    <View style={{ flex: 1, height: 260, padding: 8 }}>
      <CartesianChart
        data={pts}
        xKey="x"
        yKeys={["y"]}
        axisOptions={axisOptions}
        chartPressState={state}
      >
        {({ points }) => {
          // points.y: Cartesian 좌표계로 변환된 스크린 좌표들
          const linePts = points.y;

          // Skia Path 생성
          const path = Skia.Path.Make();
          for (let i = 0; i < linePts.length; i++) {
            const p = linePts[i];
            if (i === 0) path.moveTo(p.x, p.y);
            else path.lineTo(p.x, p.y);
          }

          // BUY/SELL 마커 대상 좌표 매칭
          const idxByX = new Map<number, { x: number; y: number }>();
          for (const p of linePts) idxByX.set(p.x, p);

          return (
            <>
              {/* 라인 그리기 */}
              <Path path={path} color="dodgerblue" style="stroke" strokeWidth={2} />

              {/* BUY 마커 (초록) */}
              {buys.map((p, i) => {
                const target = idxByX.get(p.x);
                if (!target) return null;
                return <Circle key={`buy-${i}`} cx={target.x} cy={target.y} r={4} color="#16a34a" />;
              })}

              {/* SELL 마커 (빨강) */}
              {sells.map((p, i) => {
                const target = idxByX.get(p.x);
                if (!target) return null;
                return <Circle key={`sell-${i}`} cx={target.x} cy={target.y} r={4} color="#dc2626" />;
              })}
            </>
          );
        }}
      </CartesianChart>
    </View>
  );
}
