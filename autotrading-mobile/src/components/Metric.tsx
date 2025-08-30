import { View, Text } from "react-native";

export default function Metric({ label, value }: { label: string; value: string; }) {
  return (
    <View style={{ padding: 12, borderWidth: 1, borderColor: "#eee", borderRadius: 12 }}>
      <Text style={{ color: "#666", fontSize: 12 }}>{label}</Text>
      <Text style={{ fontWeight: "700", fontSize: 18 }}>{value}</Text>
    </View>
  );
}
