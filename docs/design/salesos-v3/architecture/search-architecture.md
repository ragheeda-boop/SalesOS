# Search Architecture

Search is a **system**, not an input.

## Modes

| Mode | Returns | Notes |
|------|---------|-------|
| Universal | Mixed ranked results | Default CmdK / `/` |
| Object | Typed entities | Filter chips |
| Command | Actions | Create, navigate, admin |
| People | Contacts + Employees | |
| Company | Accounts | |
| Document | Files + knowledge chunks | Permission-filtered |
| AI / Semantic | Passages + citations | Preview when flag off shows upgrade empty |
| Recent | Last opened | Local + server |
| Saved | Saved searches | |

## UX

- Debounced query; keyboard select; enter opens.
- Permission filtering server-side.
- Empty: Search Empty state with suggestions.
- Metrics: Search Success = query → object open ≤30s.

## Legacy

`/search`, `/search/analytics` map into Universal + analytics on Search domain.
