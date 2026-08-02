# STORY-10-03 — Workflow Builder canvas → Workflow Engine (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> No second interpreter — compiles to existing `domains.workflow.WorkflowEngine`.

## Landed

| Piece | Detail |
|-------|--------|
| Canvas | `WorkflowCanvas` / `CanvasNode` (action + branch) |
| Compiler | `compile_canvas` → `Workflow` / `WorkflowStep` (`if_else` nests) |
| Store | `MemWorkflowCanvasStore` tenant-scoped |
| HTTP | `POST/GET /api/v1/studio/workflows` + `…/compile` |
| Tests | Linear compile, for_each reject, branch nest, **equivalence** vs hand-coded |

## Acceptance

Canvas-to-execution-graph compiler passes equivalence suite — covered by
`test_compiled_canvas_equivalent_to_hand_coded_execution`.

## Non-goals

- `for_each` / loop canvas nodes (Sprint-13 debt — deferred)
- FE `/studio/workflows` page wire-up — **LANDED FE-S10-03** (Stream B)
- Postgres canvas persistence / new RLS
- Production GO
