// app/_layout.tsx
import "react-native-gesture-handler";   // ① 제스처: 최상단
import "react-native-reanimated";        // ② Reanimated: 최상단

import { Stack } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <Stack screenOptions={{ headerShown: false }}>
          {/* 탭 라우터를 쓰면 (tabs) 등록 */}
          <Stack.Screen name="(tabs)" />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
