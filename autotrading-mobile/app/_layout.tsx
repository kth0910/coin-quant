import { Tabs, Slot } from "expo-router";
import { useEffect } from "react";

export default function RootLayout() {
  useEffect(() => { /* initNotifications(); */ }, []);
  return (
    <Tabs screenOptions={{ headerTitleAlign: "center" }}>
      <Tabs.Screen name="(tabs)" options={{ href: null, headerShown: false }} />
      {/* 필요 시 모달/딥링크 페이지를 추가하려면 <Slot/> 사용 */}
    </Tabs>
  );
}
