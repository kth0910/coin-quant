import { VictoryChart, VictoryLine, VictoryTheme, VictoryAxis } from "victory";
import { View } from "react-native";
import type { Signal } from "@/types";

export default function CandleLike({ data }: { data: Signal[] }) {
  const line = data.map((d, i) => ({ x: i + 1, y: d.price }));
  return (
    <View>
      <VictoryChart theme={VictoryTheme.material} domainPadding={{ x: 20, y: 10 }}>
        <VictoryAxis />
        <VictoryAxis dependentAxis />
        <VictoryLine data={line} />
      </VictoryChart>
    </View>
  );
}
