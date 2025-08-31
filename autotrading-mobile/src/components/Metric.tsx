import { View, Text } from "react-native";

type Props = { label: string; value: string; };

export default function Metric({ label, value }: Props) {
  return (
    <View style={{ padding: 12, borderWidth: 1, borderRadius: 8 }}>
      <Text style={{ fontWeight: "600" }}>{label}</Text>
      <Text>{value}</Text>
    </View>
  );
}
