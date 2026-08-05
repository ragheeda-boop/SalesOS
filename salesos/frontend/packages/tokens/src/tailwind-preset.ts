/**
 * SalesOS Tailwind Preset — Generated from tokens.ts
 *
 * Use this in your tailwind.config.ts:
 *
 *   import { preset } from "@salesos/tokens/tailwind";
 *   export default { ...preset, content: [...] }
 */

import type { Config } from 'tailwindcss'

import {
  brand,
  orange,
  neutral,
  success,
  warning,
  danger,
  info,
  fontFamily,
  fontSize,
  space,
  layout,
  radius,
  shadow,
  zIndex,
} from './tokens'

/** Mutable font stacks — Tailwind theme types reject `readonly` token arrays. */
const themeFontFamily = {
  display: [...fontFamily.display],
  sans: [...fontFamily.sans],
  arabic: [...fontFamily.arabic],
  mono: [...fontFamily.mono],
}

/** Mutable fontSize entries — same readonly/`as const` mismatch. */
const themeFontSize = Object.fromEntries(
  (Object.keys(fontSize) as Array<keyof typeof fontSize>).map((key) => {
    const [size, conf] = fontSize[key]
    return [key, [size, { lineHeight: conf.lineHeight }] as [string, { lineHeight: string }]]
  }),
)

/** Tailwind zIndex theme expects string values. */
const themeZIndex = Object.fromEntries(
  Object.entries(zIndex).map(([key, value]) => [key, String(value)]),
)

export const preset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        muhide: brand,
        orange,
        neutral,
        success,
        warning,
        danger,
        info,
      },
      fontFamily: themeFontFamily,
      fontSize: themeFontSize,
      spacing: {
        ...space,
        sidebar: layout.sidebar,
        'sidebar-collapsed': layout.sidebarCollapsed,
        topbar: layout.topbar,
        copilot: layout.copilot,
        command: layout.command,
      },
      borderRadius: { ...radius },
      boxShadow: {
        'muhide-1': shadow.muhide1,
        'muhide-2': shadow.muhide2,
        'muhide-3': shadow.muhide3,
        'muhide-4': shadow.muhide4,
        'muhide-5': shadow.muhide5,
        'muhide-6': shadow.muhide6,
      },
      zIndex: themeZIndex,
    },
  },
}

export default preset
