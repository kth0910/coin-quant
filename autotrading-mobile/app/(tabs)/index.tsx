// app/(tabs)/index.tsx
import { View, Text, ScrollView } from "react-native";
import { useSignals } from "@/hooks/useSignals";
import Metric from "@/components/Metric";
import CandleLike from "@/charts/CandleLike";

export default function Dashboard() {
  const { signals, loading } = useSignals();
  const last = signals[signals.length - 1];

  // CandleLike가 요구하는 최소 형태로 변환
  const chartData = signals.slice(-120).map(s => ({
    ts: s.ts, price: s.price, type: s.type as any
  }));

  return (
    <ScrollView contentContainerStyle={{ paddingTop: 60, paddingHorizontal: 16, gap: 12 }}>
      <Text style={{ fontSize: 22, fontWeight: "700" }}>Dashboard</Text>

      <View style={{ flexDirection: "row", gap: 12 }}>
        <Metric
          label="Latest Price"
          value={
            last ? `₩${Math.round(last.price).toLocaleString()}`
                 : (loading ? "..." : "-")
          }
        />
        <Metric
          label="Last Signal"
          value={
            last ? `${last.type} (${last.confidence})`
                 : (loading ? "..." : "-")
          }
        />
      </View>

      <CandleLike data={chartData} />
    </ScrollView>
  );
}
