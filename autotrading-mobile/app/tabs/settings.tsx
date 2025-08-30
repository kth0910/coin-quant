import { View, Text, TextInput, Button, Alert } from "react-native";
import React from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API, setApiBase } from "@/api/config";

export default function Settings() {
  const [base, setBase] = React.useState(API.base);

  return (
    <View style={{ paddingTop: 60, paddingHorizontal: 16, gap: 8 }}>
      <Text style={{ fontSize: 22, fontWeight: "700" }}>Settings</Text>
      <Text style={{ color: "#666" }}>Backend URL</Text>
      <TextInput
        value={base}
        onChangeText={setBase}
        placeholder="http://<HOST>:8000"
        autoCapitalize="none"
        style={{ borderWidth: 1, borderColor: "#ddd", padding: 10, borderRadius: 8 }}
      />
      <Button
        title="Save"
        onPress={async () => {
          await AsyncStorage.setItem("apiBase", base);
          setApiBase(base);
          Alert.alert("Saved", base);
        }}
      />
      <Button
        title="Ping /health"
        onPress={async () => {
          try {
            const r = await fetch(`${API.base}/health`);
            const j = await r.json();
            Alert.alert("Health", JSON.stringify(j));
          } catch (e) {
            Alert.alert("Error", String(e as Error));
          }
        }}
      />
    </View>
  );
}
