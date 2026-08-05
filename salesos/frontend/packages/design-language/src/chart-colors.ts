export interface ChartColorPalette {
  1: string;
  2: string;
  3: string;
  4: string;
  5: string;
  6: string;
  7: string;
  8: string;
  9: string;
  10: string;
  11: string;
  12: string;
}

export const CHART_COLORS: Record<"light" | "dark", ChartColorPalette> = {
  light: {
    1: "#F57C1E",
    2: "#22C55E",
    3: "#F59E0B",
    4: "#EF4444",
    5: "#A855F7",
    6: "#3B82F6",
    7: "#F97316",
    8: "#16A34A",
    9: "#D97706",
    10: "#DC2626",
    11: "#9333EA",
    12: "#2563EB",
  },
  dark: {
    1: "#FF9A4A",
    2: "#4ADE80",
    3: "#FBBF24",
    4: "#F87171",
    5: "#C084FC",
    6: "#60A5FA",
    7: "#FB923C",
    8: "#22C55E",
    9: "#EAB308",
    10: "#EF4444",
    11: "#A855F7",
    12: "#3B82F6",
  },
};

export const CHART_COLORS_CSS_VARS: Record<number, string> = {
  1: "var(--chart-1)",
  2: "var(--chart-2)",
  3: "var(--chart-3)",
  4: "var(--chart-4)",
  5: "var(--chart-5)",
  6: "var(--chart-6)",
  7: "var(--chart-7)",
  8: "var(--chart-8)",
  9: "var(--chart-9)",
  10: "var(--chart-10)",
  11: "var(--chart-11)",
  12: "var(--chart-12)",
};
