// src/charts/CandleLike.tsx
import React from "react";
import { View } from "react-native";

// ✅ 핵심: victory-native는 와일드카드로 받고, default fallback 처리
import * as Vraw from "victory-native";
const V: any = (Vraw as any).default ?? Vraw;

// ✅ 테마/유틸은 core victory에서
import { VictoryTheme } from "victory";

/** signals에서 쓰는 타입 최소 정의 */
type Signal = {
  price: number;
  ts: string;            // ISO 문자열 가정
};

/** props: signals 배열을 받음 */
export default function CandleLike({ data }: { data: Signal[] }) {
  // Victory가 먹을 수 있게 {x,y} 형태로 변환
  const line = data.map((d, i) => ({ x: i + 1, y: d.price }));

  // (디버그) 실제로 무엇이 들어왔는지 확인하고 싶으면 한 번만 열어보기
  // console.log("Victory-native keys:", Object.keys(V));

  return (
    <View style={{ paddingVertical: 8 }}>
      <V.VictoryChart theme={VictoryTheme.material} domainPadding={{ x: 15, y: 10 }}>
        <V.VictoryAxis />
        <V.VictoryLine data={line} />
      </V.VictoryChart>
    </View>
  );
}
