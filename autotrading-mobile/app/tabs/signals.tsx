import { View, Text, FlatList, RefreshControl } from "react-native";
import { useSignals } from "@/hooks/useSignals";
import SignalCard from "@/components/SignalCard";

export default function Signals() {
  const { signals, loading } = useSignals();

  return (
    <View style={{ paddingTop: 60, paddingHorizontal: 16, flex: 1 }}>
      <Text style={{ fontSize: 22, fontWeight: "700", marginBottom: 8 }}>Signals</Text>
      <FlatList
        data={[...signals].reverse()}
        keyExtractor={(x) => String(x.id ?? Math.random())}
        renderItem={({ item }) => <SignalCard s={item} />}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={() => { /* WS 기반: noop */ }} />}
      />
    </View>
  );
}
