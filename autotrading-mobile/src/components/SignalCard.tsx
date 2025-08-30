import { View, Text } from "react-native";
import type { Signal } from "@/types";

export default function SignalCard({ s }: { s: Signal }) {
  const color = s.type === "BUY" ? "#16a34a" : s.type === "SELL" ? "#dc2626" : "#374151";
  return (
    <View style={{ paddingVertical: 10, borderBottomWidth: 0.5, borderColor: "#eee" }}>
      <Text style={{ color: "#888", marginBottom: 4 }}>{new Date(s.ts).toLocaleString()}</Text>
      <Text style={{ fontWeight: "700", color }}>
        {s.type} {s.ticker}  ₩{Math.round(s.price).toLocaleString()}  (conf {s.confidence})
      </Text>
      <Text numberOfLines={2} style={{ color: "#555" }}>{s.reason}</Text>
    </View>
  );
}
