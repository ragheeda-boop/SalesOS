# AI Experience Program (Phase 7)

Honesty: [AI_HONESTY.md](../../audit/ga-engineering-audit/AI_HONESTY.md). Default Preview when `feature_ai_copilot=false`.

## Layout rule (locked)

**AI is never part of the page layout.** No permanent rail, half-page panel, or dedicated tab body that consumes workspace chrome.

- Entry: topbar **Ask AI** button, `Ctrl+Shift+A`, or `openV3AiPopup({ contextLabel })`
- Surface: **modal popup only** (`V3AiPopup`)
- Product pages stay full-width for human work (lists, 360 tabs, grids)

## Capabilities

| Capability | Description |
|------------|-------------|
| Conversation | Global Ask AI **popup** |
| Actions | Tool calls requiring **Human Approval** when side-effecting |
| Predictions | Forecast / churn scores with confidence |
| Recommendations | NBA, matching |
| Explainability | Why this suggestion |
| Confidence | Numeric + qualitative |
| Sources | Citations / evidence links |
| Preview | Badge inside popup |
| Human Approval | Modal/sheet gate |
| Audit | All AI actions logged |
| Memory | Workspace-scoped, retention settings |
| Reasoning | Optional expandable trace (admin) |
| Feedback | Thumbs + comment |
| Evaluation | Offline eval scores before GA |

## UX rules

- Never silent autonomous writes in Preview.
- Always show sources when claiming facts.
- Decision Center remains human-decides.
- Do not embed AI summaries as primary page regions.
 before GA |

## UX rules

- Never silent autonomous writes in Preview.
- Always show sources when claiming facts.
- Decision Center remains human-decides.
- Do not market stub FE decision packages as live GA AI.
- Settings → AI section configures prefs only; it does not host a chat pane in-page.

## Screens

AI Assistant (popup) · Prompt Library · Copilot · Recommendations · Auto Insights · Agent Center · Knowledge Search · Meeting Summary · Email Generator · Forecast Generator — all Preview-capable; **Assistant entry is always modal**, never chrome rail.
