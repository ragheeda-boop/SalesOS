import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
      "./packages/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        muhide: {
          orange: "#F57C1E",
          ink: "#151214",
          espresso: "#403D38",
          sand: "#CCC6BA",
          paper: "#FAFAFA",
        },
        orange: {
          50: "#FFF3E6", 100: "#FFE2BF", 200: "#FFCE99", 300: "#FFB870",
          400: "#FFA04A", 500: "#F57C1E", 600: "#D4660F", 700: "#B35009",
          800: "#8F3C06", 900: "#6E2A03",
        },
        neutral: {
          50: "#F7F6F4", 100: "#EDEBE6", 200: "#D9D5CD", 300: "#BFB9AD",
          400: "#A59E90", 500: "#8B8475", 600: "#706A5D", 700: "#565147",
          800: "#3D3932", 900: "#26231E",
        },
        success: {
          50: "#E8F5E9", 100: "#C8E6C9", 200: "#A5D6A7", 300: "#81C784",
          400: "#66BB6A", 500: "#4CAF50", 600: "#388E3C", 700: "#2E7D32",
          800: "#1B5E20", 900: "#0D3B0F",
        },
        warning: {
          50: "#FFF8E1", 100: "#FFECB3", 200: "#FFE082", 300: "#FFD54F",
          400: "#FFCA28", 500: "#FFC107", 600: "#FFB300", 700: "#FFA000",
          800: "#FF8F00", 900: "#E65100",
        },
        danger: {
          50: "#FFEBEE", 100: "#FFCDD2", 200: "#EF9A9A", 300: "#E57373",
          400: "#EF5350", 500: "#F44336", 600: "#E53935", 700: "#D32F2F",
          800: "#C62828", 900: "#B71C1C",
        },
        info: {
          50: "#E3F2FD", 100: "#BBDEFB", 200: "#90CAF9", 300: "#64B5F6",
          400: "#42A5F5", 500: "#2196F3", 600: "#1E88E5", 700: "#1976D2",
          800: "#1565C0", 900: "#0D47A1",
        },
      },
      fontFamily: {
        display: ["Viga", "IBM Plex Sans Arabic", "sans-serif"],
        sans: ["IBM Plex Sans", "sans-serif"],
        arabic: ["IBM Plex Sans Arabic", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      fontSize: {
        xs: ["11px", "1.4"],
        sm: ["12px", "1.4"],
        base: ["14px", "1.6"],
        lg: ["16px", "1.5"],
        xl: ["18px", "1.35"],
        "2xl": ["20px", "1.3"],
        "3xl": ["24px", "1.2"],
        "4xl": ["32px", "1.15"],
      },
      spacing: {
        sidebar: "256px",
        "sidebar-collapsed": "64px",
        topbar: "56px",
        copilot: "384px",
        command: "576px",
      },
      borderRadius: {
        sm: "2px",
        md: "6px",
        lg: "8px",
        xl: "12px",
        "2xl": "16px",
      },
      boxShadow: {
        "muhide-1": "0 1px 2px rgba(21,18,20,0.06)",
        "muhide-2": "0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)",
        "muhide-3": "0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)",
        "muhide-4": "0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)",
        "muhide-5": "0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)",
        "muhide-6": "0 25px 50px rgba(21,18,20,0.16)",
      },
      zIndex: {
        dropdown: "10",
        sticky: "20",
        banner: "30",
        overlay: "40",
        modal: "50",
        toast: "60",
      },
    },
  },
  plugins: [],
};

export default config;
