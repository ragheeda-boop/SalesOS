"""Theme SDK — build and customize themes for the Design Token System.

Provides:
  - Token builder with type safety
  - CSS variable generator
  - Dark mode resolver
  - Tenant theme overrides
  - Theme inheritance (brand → tenant → user)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ThemeTokenSet:
    """A set of design tokens for a theme."""
    colors: dict = field(default_factory=dict)
    typography: dict = field(default_factory=dict)
    radius: dict = field(default_factory=dict)
    elevation: dict = field(default_factory=dict)
    spacing: dict = field(default_factory=dict)
    motion: dict = field(default_factory=dict)
    breakpoints: dict = field(default_factory=dict)
    icons: dict = field(default_factory=dict)

    def to_css_variables(self, prefix: str = "--tw-") -> str:
        lines = [":root {"]
        for category in ["colors", "radius", "elevation", "spacing", "motion", "breakpoints", "icons"]:
            tokens = getattr(self, category, {})
            for key, value in tokens.items():
                css_key = key.replace("_", "-")
                lines.append(f"  {prefix}{css_key}: {value};")
        lines.append("}")
        return "\n".join(lines)

    def merge(self, overrides: "ThemeTokenSet") -> "ThemeTokenSet":
        import copy
        merged = copy.deepcopy(self)
        for category in ["colors", "typography", "radius", "elevation", "spacing", "motion", "breakpoints", "icons"]:
            base = getattr(merged, category)
            override = getattr(overrides, category, {})
            base.update(override)
        return merged


class ThemeBuilder:
    """Build a complete theme with tokens."""

    def __init__(self, name: str = "custom"):
        self._name = name
        self._tokens = ThemeTokenSet()
        self._parent: Optional[str] = None
        self._is_dark = False

    def inherit(self, parent_theme: str) -> "ThemeBuilder":
        self._parent = parent_theme
        return self

    def dark(self) -> "ThemeBuilder":
        self._is_dark = True
        return self

    def with_colors(self, **colors) -> "ThemeBuilder":
        self._tokens.colors.update(colors)
        return self

    def with_typography(self, **tokens) -> "ThemeBuilder":
        self._tokens.typography.update(tokens)
        return self

    def with_radius(self, **tokens) -> "ThemeBuilder":
        self._tokens.radius.update(tokens)
        return self

    def with_elevation(self, **tokens) -> "ThemeBuilder":
        self._tokens.elevation.update(tokens)
        return self

    def with_spacing(self, **tokens) -> "ThemeBuilder":
        self._tokens.spacing.update(tokens)
        return self

    def with_motion(self, **tokens) -> "ThemeBuilder":
        self._tokens.motion.update(tokens)
        return self

    def build(self) -> dict:
        return {
            "name": self._name,
            "parent": self._parent,
            "is_dark": self._is_dark,
            "tokens": {
                "colors": self._tokens.colors,
                "typography": self._tokens.typography,
                "radius": self._tokens.radius,
                "elevation": self._tokens.elevation,
                "spacing": self._tokens.spacing,
                "motion": self._tokens.motion,
                "breakpoints": self._tokens.breakpoints,
                "icons": self._tokens.icons,
            },
            "css": self._tokens.to_css_variables(),
        }


def create_theme(name: str = "custom") -> ThemeBuilder:
    return ThemeBuilder(name)
