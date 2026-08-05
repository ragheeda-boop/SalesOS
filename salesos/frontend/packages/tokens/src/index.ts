/**
 * @salesos/tokens — SalesOS Design Tokens
 *
 * Single source of truth for all design decisions.
 * Import from this file in TypeScript/JavaScript:
 *
 *   import { brand, orange, neutral, space, motion } from "@salesos/tokens";
 *
 * For CSS variables, import the CSS file:
 *
 *   @import "@salesos/tokens/css";
 *
 * For Tailwind, use the preset:
 *
 *   import { preset } from "@salesos/tokens/tailwind";
 */

export {
  // Brand
  brand,

  // Color scales
  orange,
  neutral,
  success,
  warning,
  danger,
  info,

  // Semantic colors
  semanticLight,
  semanticDark,
  status,

  // Chart colors
  chart,

  // Typography
  fontFamily,
  fontSize,
  fontWeight,

  // Spacing
  space,
  layout,

  // Border radius
  radius,

  // Shadows
  shadow,

  // Z-index
  zIndex,

  // Motion
  motion,

  // Focus
  focus,

  // All tokens (namespace)
  tokens,

  // Type
  type Tokens,
} from './tokens'
