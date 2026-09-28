"""ThemeTokenSet.to_css_variables()'s category list independently duplicated
merge()'s list of the dataclass's 8 field names, and the two copies drifted:
to_css_variables()'s list omitted "typography" -- present in the dataclass
fields and in merge()'s own (correct) copy of the same list -- so every
typography token set via ThemeBuilder.with_typography(...) was silently
dropped from the generated CSS output, with no error.

Fixed by extracting a single shared _TOKEN_CATEGORIES constant used by
both methods, so the two can no longer independently drift.
"""

from __future__ import annotations

from sdk.theme_sdk import ThemeTokenSet, create_theme


def test_to_css_variables_includes_typography_tokens() -> None:
    theme = create_theme("brand").with_typography(base_size="16px", scale_ratio="1.25").build()

    assert "--tw-base-size: 16px;" in theme["css"]
    assert "--tw-scale-ratio: 1.25;" in theme["css"]


def test_to_css_variables_includes_every_declared_category() -> None:
    """All 8 dataclass fields must be represented, not just some of them."""
    tokens = ThemeTokenSet(
        colors={"primary": "#000"},
        typography={"font": "Inter"},
        radius={"sm": "4px"},
        elevation={"card": "0 1px 2px"},
        spacing={"md": "8px"},
        motion={"fast": "150ms"},
        breakpoints={"sm": "640px"},
        icons={"size": "16px"},
    )
    css = tokens.to_css_variables()
    for expected in (
        "--tw-primary: #000;",
        "--tw-font: Inter;",
        "--tw-sm: 4px;",
        "--tw-card: 0 1px 2px;",
        "--tw-md: 8px;",
        "--tw-fast: 150ms;",
        "--tw-size: 16px;",
    ):
        assert expected in css, f"missing {expected!r} in generated CSS: {css!r}"
    # "breakpoints" also has key "sm", same as radius -- assert the count
    # of "--tw-sm:" occurrences to prove both categories' entries emitted.
    assert css.count("--tw-sm:") == 2


def test_merge_still_merges_typography_correctly() -> None:
    """Regression guard: the shared constant refactor must not change
    merge()'s already-correct behavior."""
    base = ThemeTokenSet(typography={"font": "Inter"})
    override = ThemeTokenSet(typography={"weight": "700"})
    merged = base.merge(override)
    assert merged.typography == {"font": "Inter", "weight": "700"}
