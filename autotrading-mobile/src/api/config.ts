import Constants from "expo-constants";

const base = (Constants.expoConfig as any)?.extra?.apiBase;
if (!base) {
  throw new Error("⚠️ apiBase가 expoConfig.extra.apiBase에 정의되어 있지 않습니다.");
}

export const API = {
  base,
  ws: toWs(base),
};

function toWs(base: string) {
  const u = new URL(base);
  const wsProto = u.protocol === "https:" ? "wss:" : "ws:";
  return `${wsProto}//${u.host}/ws/updates`;
}
