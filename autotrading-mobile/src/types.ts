export type Signal = {
  id: number;
  type: "BUY" | "SELL" | "HOLD" | "ALERT";
  ticker: string;
  price: number;
  confidence: number;
  reason: string;
  ts: string;          // ISO
};
