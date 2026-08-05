export interface SemanticTokenMap {
  light: Record<string, string>;
  dark: Record<string, string>;
}

/**
 * Complete semantic token map for light and dark modes.
 * These are the CSS variable values that get applied via :root and .dark classes.
 */
export const SEMANTIC_TOKENS: SemanticTokenMap = {
  light: {
    "--bg-primary": "#FAFAFA",
    "--bg-secondary": "#F5F4F2",
    "--bg-tertiary": "#EDEBE6",
    "--surface-card": "#FFFFFF",
    "--surface-sidebar": "#F5F4F2",
    "--surface-modal": "#FFFFFF",
    "--border-default": "#CCC6BA",
    "--border-muted": "#D9D5CD",
    "--text-primary": "#151214",
    "--text-secondary": "#403D38",
    "--text-muted": "#8C8374",
    "--muhide-orange": "#F57C1E",
    "--chart-1": "#F57C1E",
    "--chart-2": "#22C55E",
    "--chart-3": "#F59E0B",
    "--chart-4": "#EF4444",
    "--chart-5": "#A855F7",
    "--chart-6": "#3B82F6",
    "--chart-7": "#F97316",
    "--chart-8": "#16A34A",
    "--chart-9": "#D97706",
    "--chart-10": "#DC2626",
    "--chart-11": "#9333EA",
    "--chart-12": "#2563EB",
  },
  dark: {
    "--bg-primary": "#151214",
    "--bg-secondary": "#1A181B",
    "--bg-tertiary": "#26231E",
    "--surface-card": "#1E1C1F",
    "--surface-sidebar": "#1A181B",
    "--surface-modal": "#1E1C1F",
    "--border-default": "#3D393C",
    "--border-muted": "#565147",
    "--text-primary": "#FAFAFA",
    "--text-secondary": "#BFB9AD",
    "--text-muted": "#A59E90",
    "--muhide-orange": "#F57C1E",
    "--chart-1": "#FF9A4A",
    "--chart-2": "#4ADE80",
    "--chart-3": "#FBBF24",
    "--chart-4": "#F87171",
    "--chart-5": "#C084FC",
    "--chart-6": "#60A5FA",
    "--chart-7": "#FB923C",
    "--chart-8": "#22C55E",
    "--chart-9": "#EAB308",
    "--chart-10": "#EF4444",
    "--chart-11": "#A855F7",
    "--chart-12": "#3B82F6",
  },
};

/** Generate CSS string for a given mode */
export function semanticTokensCSS(mode: "light" | "dark"): string {
  const tokens = SEMANTIC_TOKENS[mode];
  const selector = mode === "light" ? ":root" : ".dark";
  const rules = Object.entries(tokens)
    .map(([key, value]) => `  ${key}: ${value};`)
    .join("\n");
  return `${selector} {\n${rules}\n}`;
}
