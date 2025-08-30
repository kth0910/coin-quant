import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";

const defaultBase = Constants.expoConfig?.extra?.apiBase ?? "http://localhost:8000";

export const API = { base: defaultBase, ws: toWs(defaultBase) };

function toWs(base: string) {
  const u = new URL(base);
  return (u.protocol === "https:" ? "wss:" : "ws:") + "//" + u.host + "/ws/updates";
}

export async function hydrateApiBase() {
  const v = await AsyncStorage.getItem("apiBase");
  if (v) setApiBase(v);
}

export function setApiBase(base: string) {
  API.base = base;
  API.ws = toWs(base);
}
