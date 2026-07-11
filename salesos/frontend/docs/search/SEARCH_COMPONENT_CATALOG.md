# Universal Search Platform — Component Catalog

> Every Search component, its props, states, and responsibilities.

## SearchBar
Top-level search bar. Can render as input-only or with filters/suggestions dropdown.

| Prop | Type | Default |
|------|------|---------|
| value | string | '' |
| onChange | (value: string) => void | required |
| onSearch | (query: SearchQuery) => void | required |
| placeholder | string | 'ابحث في المنصة…' |
| variant | 'default' \| 'minimal' \| 'hero' | 'default' |
| filters | SearchFilter[] | [] |
| loading | boolean | false |
| autoFocus | boolean | false |

States: default, focused, loading, error

## SearchInput
Raw input with debounce, clear button, icon.

## SearchResultCard
Single result. Entity type icon, title, subtitle, badges, score, actions.

| State | Behavior |
|-------|----------|
| loading | Skeleton pulse |
| empty | Hidden (handled by parent) |
| success | Full card with highlights |
| error | Fallback message |

## SearchSection
Groups results by entity type. Collapsible header with count.

## SearchGroup
Nested grouping (e.g. "Suppliers → Active" inside Company).

## SearchFilters
Filter sidebar. Facets with counts. Multi-select, range sliders.

## SearchBadge
Entity type or status badge. 5 variants.

## SearchHighlight
Text with `<mark>` tags from highlight snippets.

## SearchEmpty
Centered illustration + message + suggestion to refine.

## SearchLoading
Skeleton results matching last result shape.

## SearchError
Error card with retry button.

## SearchSuggestion
Single suggestion row with icon, text, source.

## SearchHistory
Recents grouped by time. Clearable.

## SearchFacet
Single facet group. Expandable with value counts.

## SearchPill
Active filter pill. Removable.

## SearchHeader
Page header with title, count, sort dropdown, view toggle.
