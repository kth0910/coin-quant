// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],           // ✅ 여기에 expo-router 지원 내장
    plugins: [
      "expo-router/babel",
      "react-native-reanimated/plugin", // ← 이걸로 되돌리세요 (배열의 마지막에 두는 게 권장)
    ],
  };
};
