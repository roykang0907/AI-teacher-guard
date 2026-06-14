import type { Label } from "./types";

export const labelColor: Record<Label, string> = {
  정상: "bg-green-100 text-green-800 border-green-300",
  주의: "bg-amber-100 text-amber-800 border-amber-300",
  위험: "bg-red-100 text-red-800 border-red-300",
};

export const labelDot: Record<Label, string> = {
  정상: "bg-green-500",
  주의: "bg-amber-500",
  위험: "bg-red-500",
};

export function intensityBars(n: number): string {
  return "●".repeat(n) + "○".repeat(Math.max(0, 3 - n));
}
