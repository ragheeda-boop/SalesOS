"""Design Token System — the visual foundation for every tenant.

Brand
└── Design Tokens
    ├── Colors (primary, neutral, semantic, chart)
    ├── Typography (family, scale, weight, line-height)
    ├── Radius (none, sm, md, lg, full, pill)
    ├── Elevation (shadows: sm, md, lg, xl)
    ├── Spacing (4, 8, 12, 16, 24, 32, 48, 64)
    ├── Icons (library reference + naming)
    ├── Motion (easing, duration, transitions)
    └── Breakpoints (sm, md, lg, xl)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ── Color Tokens ──────────────────────────────────────────────

@dataclass
class ColorPalette:
    primary: str = "#F57C1E"       # muhide-orange (was #2563EB blue-600)
    primary_light: str = "#FFA04A" # orange-400 (was #3B82F6 blue-500)
    primary_dark: str = "#D4660F"  # orange-600 (was #1D4ED8 blue-700)
    primary_contrast: str = "#FFFFFF"

    neutral_50: str = "#F7F6F4"
    neutral_100: str = "#EDEBE6"
    neutral_200: str = "#D9D5CD"
    neutral_300: str = "#BFB9AD"
    neutral_400: str = "#A59E90"
    neutral_500: str = "#8B8475"
    neutral_600: str = "#706A5D"
    neutral_700: str = "#565147"
    neutral_800: str = "#3D3932"
    neutral_900: str = "#26231E"
    neutral_950: str = "#1A1714"

    success: str = "#4CAF50"       # green-500
    warning: str = "#FFC107"       # amber-500
    error: str = "#F44336"         # red-500
    info: str = "#2196F3"          # blue-500 (reserved for focus rings, links)

    chart_1: str = "#F57C1E"
    chart_2: str = "#4CAF50"
    chart_3: str = "#FFC107"
    chart_4: str = "#F44336"
    chart_5: str = "#8B5CF6"
    chart_6: str = "#2196F3"

    surface: str = "#FFFFFF"
    surface_secondary: str = "#F7F6F4"
    surface_tertiary: str = "#EDEBE6"
    border: str = "#D9D5CD"
    border_strong: str = "#BFB9AD"
    text_primary: str = "#26231E"
    text_secondary: str = "#706A5D"
    text_tertiary: str = "#A59E90"
    text_disabled: str = "#BFB9AD"
    text_inverse: str = "#FFFFFF"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


# ── Typography Tokens ─────────────────────────────────────────

@dataclass
class TypographyTokens:
    font_family_arabic: str = "'IBM Plex Sans Arabic', sans-serif"
    font_family_english: str = "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    font_family_display: str = "'Viga', 'IBM Plex Sans Arabic', sans-serif"
    font_family_mono: str = "'IBM Plex Mono', monospace"

    # Font sizes (rem)
    scale: dict = field(default_factory=lambda: {
        "xs": "0.6875rem",   # 11px
        "sm": "0.75rem",     # 12px
        "base": "0.875rem",  # 14px
        "lg": "1rem",        # 16px
        "xl": "1.125rem",    # 18px
        "2xl": "1.25rem",    # 20px
        "3xl": "1.5rem",     # 24px
        "4xl": "2rem",       # 32px
    })

    font_weight: dict = field(default_factory=lambda: {
        "regular": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700",
    })

    line_height: dict = field(default_factory=lambda: {
        "tight": "1.25",
        "normal": "1.5",
        "relaxed": "1.75",
    })

    letter_spacing: dict = field(default_factory=lambda: {
        "tight": "-0.025em",
        "normal": "0",
        "wide": "0.025em",
    })

    def to_dict(self) -> dict:
        return {
            "font_family_arabic": self.font_family_arabic,
            "font_family_english": self.font_family_english,
            "font_family_mono": self.font_family_mono,
            "scale": self.scale,
            "font_weight": self.font_weight,
            "line_height": self.line_height,
            "letter_spacing": self.letter_spacing,
        }


# ── Radius Tokens ─────────────────────────────────────────────

@dataclass
class RadiusTokens:
    none: str = "0"
    sm: str = "2px"
    md: str = "6px"
    lg: str = "8px"
    xl: str = "12px"
    full: str = "9999px"
    pill: str = "9999px"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ── Elevation (Shadow) Tokens ─────────────────────────────────

@dataclass
class ElevationTokens:
    sm: str = "0 1px 2px rgba(21,18,20,0.06)"
    md: str = "0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)"
    lg: str = "0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)"
    xl: str = "0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)"
    drawer: str = "-8px 0 20px rgba(21,18,20,0.15)"
    modal: str = "0 25px 50px rgba(21,18,20,0.16)"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ── Spacing Tokens ────────────────────────────────────────────

@dataclass
class SpacingTokens:
    scale: dict = field(default_factory=lambda: {
        "0": "0",
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
        "20": "80px",
        "24": "96px",
    })

    # Semantic spacing
    page_horizontal: str = "24px"
    page_vertical: str = "24px"
    section_gap: str = "24px"
    card_padding: str = "16px"
    widget_gap: str = "16px"
    list_item_gap: str = "12px"

    def to_dict(self) -> dict:
        return {
            "scale": self.scale,
            "page_horizontal": self.page_horizontal,
            "page_vertical": self.page_vertical,
            "section_gap": self.section_gap,
            "card_padding": self.card_padding,
            "widget_gap": self.widget_gap,
            "list_item_gap": self.list_item_gap,
        }


# ── Icon Tokens ───────────────────────────────────────────────

@dataclass
class IconTokens:
    library: str = "lucide-react"  # standard icon library
    size_sm: str = "16px"
    size_md: str = "20px"
    size_lg: str = "24px"
    size_xl: str = "32px"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ── Motion Tokens ─────────────────────────────────────────────

@dataclass
class MotionTokens:
    duration_fast: str = "150ms"
    duration_normal: str = "200ms"
    duration_slow: str = "300ms"
    easing_linear: str = "linear"
    easing_in: str = "cubic-bezier(0.4, 0, 1, 1)"
    easing_out: str = "cubic-bezier(0, 0, 0.2, 1)"
    easing_in_out: str = "cubic-bezier(0.4, 0, 0.2, 1)"
    transition_default: str = "200ms cubic-bezier(0.4, 0, 0.2, 1)"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ── Breakpoint Tokens ─────────────────────────────────────────

@dataclass
class BreakpointTokens:
    sm: str = "640px"
    md: str = "768px"
    lg: str = "1024px"
    xl: str = "1280px"
    xxl: str = "1536px"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ── Complete Theme ────────────────────────────────────────────

@dataclass
class DesignTheme:
    name: str = "default"
    tenant_id: Optional[str] = None
    is_dark: bool = False
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    radius: RadiusTokens = field(default_factory=RadiusTokens)
    elevation: ElevationTokens = field(default_factory=ElevationTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    icons: IconTokens = field(default_factory=IconTokens)
    motion: MotionTokens = field(default_factory=MotionTokens)
    breakpoints: BreakpointTokens = field(default_factory=BreakpointTokens)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "is_dark": self.is_dark,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "radius": self.radius.to_dict(),
            "elevation": self.elevation.to_dict(),
            "spacing": self.spacing.to_dict(),
            "icons": self.icons.to_dict(),
            "motion": self.motion.to_dict(),
            "breakpoints": self.breakpoints.to_dict(),
        }

    def generate_css_variables(self) -> str:
        """Generate CSS custom properties from tokens."""
        lines = [":root {"]
        prefix = "--tw-"

        # Colors
        for k, v in self.colors.to_dict().items():
            key = k.replace("_", "-")
            lines.append(f"  {prefix}{key}: {v};")

        # Radius
        for k, v in self.radius.to_dict().items():
            lines.append(f"  {prefix}radius-{k}: {v};")

        # Elevation
        for k, v in self.elevation.to_dict().items():
            lines.append(f"  {prefix}elevation-{k}: {v};")

        # Spacing
        for k, v in self.spacing.to_dict().items():
            if k in ("scale",):
                for sk, sv in v.items():
                    lines.append(f"  {prefix}space-{sk}: {sv};")
            else:
                key = k.replace("_", "-")
                lines.append(f"  {prefix}space-{key}: {v};")

        # Typography scale
        for k, v in self.typography.scale.items():
            lines.append(f"  {prefix}text-{k}: {v};")

        lines.append("}")
        return "\n".join(lines)


# ── Theme Registry ────────────────────────────────────────────

_default_theme = DesignTheme()

THEME_REGISTRY: dict[str, DesignTheme] = {
    "default": _default_theme,
}


def get_theme(name: str = "default", tenant_id: Optional[str] = None) -> DesignTheme:
    """Get a theme by name, optionally scoped to tenant."""
    key = f"{tenant_id}:{name}" if tenant_id else name
    theme = THEME_REGISTRY.get(key)
    if theme:
        return theme
    base = THEME_REGISTRY.get(name, _default_theme)
    if tenant_id:
        # Clone for tenant override
        import copy
        theme = copy.deepcopy(base)
        theme.tenant_id = tenant_id
        THEME_REGISTRY[key] = theme
    return base


def register_theme(name: str, theme: DesignTheme):
    """Register a named theme."""
    THEME_REGISTRY[name] = theme
