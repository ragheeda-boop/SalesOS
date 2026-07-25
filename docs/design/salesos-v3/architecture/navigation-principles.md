# Navigation Principles

## Levels

| Level | Name | Examples | Chrome |
|------:|------|----------|--------|
| L1 | Workspace | Tenant, Org, Environment | Workspace switcher |
| L2 | Domain | CRM, Companies, People, CS, Analytics, Admin, AI | Sidebar sections |
| L3 | Object | Company, Deal, Contract | List / 360 |
| L4 | Action | Create, Assign, Approve, Export | CmdK, bulk bar, primary CTA |
| L5 | Context | Tab, AI rail, related list, filter | In-object chrome |

## Rules

1. **≤3 clicks** from app home to any primary object record (L1 implicit → L2 → L3).
2. L4/L5 **never** require a fourth sidebar click — use CmdK, shortcuts, sheets, record tabs.
3. Domains group modules; avoid flat 25-item lists.
4. One active domain highlight; cross-domain via CmdK/Search.
5. Deep links restore L5 context (tab query param).

## Anti-patterns

- Duplicate nav entries (legacy Contacts).
- Orphan routes without domain membership.
- Modal stacks for primary create flows (prefer sheet).
- Hiding Knowledge/Marketplace from IA.

## CmdK taxonomy

`Go to` · `Create` · `Search objects` · `Run command` · `Switch workspace` · `Ask AI` (Preview).
