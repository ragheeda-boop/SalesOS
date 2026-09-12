# 06 — MVP Scope — نطاق الحد الأدنى القابل للبيع

**Purpose:** حدد المنتج الأصغر الذي يستحق تجربة تجريبية مدفوعة أو باتفاق شريك تصميم. كل ما هو خارج هذا النطاق يُجَمَّد أو يُخفى بشكل صادق حتى يثبت الطلب.

**Guiding principle:** breadth is not shipping value; depth on one workflow is.

---

## 1. MVP Definition — Board-signable

**AR:** MVP = **"مساعد المبيعات السعودي مع دليل"** = مستأجر واحد سعودي، Companies + Contacts + Deals + Copilot Grounded + HITL Approvals + Master Data للشركة نفسها + Comm Hub Gmail وحده — على v3 shell فقط، مع Backup schedule نشط، وProduction LLM موقَّع، وPhase 7 مغلق لعينة العميل.

**EN:** MVP = **"Saudi Sales Copilot with an Evidence Trail"** = one KSA tenant, Companies + Contacts + Deals + Grounded Copilot + HITL Approvals + Master Data for that tenant only + Gmail-only Comm Hub — on the v3 shell only, with Backup schedule enabled, production LLM contract signed, and Phase 7 closed for the tenant's data slice.

---

## 2. IN-SCOPE (MVP) — 12 must-ship items

| # | Item | Status today | Gap to MVP |
|---|------|--------------|------------|
| 1 | Tenant Onboarding wizard (invite users, set locale=AR, seed ICP) | Studio pieces exist, no unified wizard | Build simple wizard on `/v3/settings` |
| 2 | Companies list + 360 view + Master Data lookup | CLOSED (Phase 1) | Enable real Muhide subset for that tenant |
| 3 | Contacts + People (Master Data linked) | CLOSED (Phase 1) | Same as #2 |
| 4 | Deals + Pipeline + Activities | CLOSED (Phase 1) | UX polish only |
| 5 | Grounded Copilot (Ask/Explain/Summarize/Investigate/Recommend) | CLOSED (Phase 3) code | **Swap AI Horde → production LLM** |
| 6 | HITL Approvals for AI recommendations | CLOSED (Phase 3) | Explicit onboarding of approver role |
| 7 | Signal Marketplace: pick ONE vertical pack that matches the tenant | 3 packs shipped (construction/healthcare/financial-services) | Choose based on ICP; pilot with 1 pack only |
| 8 | Communication Hub: Gmail sync only (skip Calendar in MVP if it delays) | CLOSED (§35 Comm Hub live) | OAuth staging in Google Cloud Console |
| 9 | Effectiveness dashboard (`/v3/effectiveness`) | CLOSED | Pilot metrics defined |
| 10 | Master Data Review Queue (`/v3/data/review-queue`) | Route exists (Phase 7) | Tenant-scoped subset from Phase 7-A output |
| 11 | Basic pricing page + Stripe live keys + Order Form + MSA + DPA | Billing spine CLOSED; docs missing | Legal + Stripe activation |
| 12 | Public status page + support email + response-time commit | UNKNOWN | Create hosted status + email + SLA-lite |

---

## 3. OUT-OF-SCOPE (MVP) — 15 explicitly parked

| # | Item | Rationale |
|---|------|-----------|
| 1 | GTM Intelligence 11-story pack (market_sizing, lookalike, outreach, sequencing, website_intelligence, verification, enrichment router) | Heavy scaffolding, low validated demand; defrost after PMF |
| 2 | Knowledge Graph (Neo4j) | OFFLINE per ADR-108; skip until v2.0 |
| 3 | Full v3 breadth of 24 nav items | Prune sales-dashboard, my-day, effectiveness only for pilot; hide employees, marketplace |
| 4 | Legacy `/(dashboard)/*` 78 routes | Deprecate visibly; do not sell |
| 5 | Decision Center advanced (multi-engine, hybrid explainability) | Residual partial per AI_HONESTY.md §8 |
| 6 | Mobile app | Product Bible P4 |
| 7 | Multi-region DR | Overkill for pilot; single-region OK |
| 8 | K8s deploy path | Quarantined per DEC-149 |
| 9 | Custom LLM fine-tuning | Not needed if provider is good |
| 10 | Employee 360 as product surface | Internal use only for now |
| 11 | Marketplace listings (developer marketplace) | Wait 10 tenants |
| 12 | Widget SDK / embeddable | Wait for design-partner signal |
| 13 | Neo4j Path analysis UI | Depends on #2 |
| 14 | Odoo / SAP integrations | Wait for validated demand |
| 15 | Multi-currency, multi-language beyond AR/EN | Wait |

---

## 4. Definition of Done (MVP)

**All 12 conditions must be TRUE and DEMONSTRABLE:**

1. [ ] One named Saudi tenant, real production tenant_id, Muhide data slice ingested to `salesos` prod (post Phase 7 for that subset)
2. [ ] Production LLM contract signed (OpenAI Enterprise / Azure OpenAI / equivalent); AI Horde removed from prod code paths
3. [ ] `feature_ai_copilot` reconciled with `AI_HONESTY.md` (one honest state)
4. [ ] `README.md` domain table rewritten to match reality (no false "🟢 Live" for KG/Copilot without conditions)
5. [ ] Railway managed backup schedule ENABLED
6. [ ] OAuth staging + production Google Cloud Console apps live
7. [ ] Stripe live keys provisioned; test transaction succeeded
8. [ ] MSA + DPA + Order Form + SLA-lite + ToS drafted and legal-reviewed
9. [ ] Public status page + support channel + response-time SLA-lite published
10. [ ] `git` working tree of `fix/login-and-keys` cleanly repaired (no 4,748 staged deletions)
11. [ ] Live browser QA pass on ≥ 10 v3 pages by an independent human (not agent)
12. [ ] One HITL-approved AI recommendation → booked activity on real production data

**Verdict criterion:** if all 12 are green → **launchable pilot MVP**. If < 8 → **not launchable**.

---

## 5. MVP-adjacent nice-to-haves (do only if trivial)

- Onboarding email templates in AR/EN
- Slack/webhook notification when HITL approval requested
- Weekly digest email (top signals, deals to review)
- One-click Muhide company import from a CSV upload

---

## 6. Scope-guard: what CANNOT enter MVP

Regardless of engineering enthusiasm, these will NOT enter MVP scope:
- Any auto-execute AI (violates HITL invariant + ADR-113/115)
- Any feature dependent on Neo4j (OFFLINE per ADR-108)
- Any feature requiring third-party live LLM before production contract signed
- Any modification that changes tenant isolation posture
- Any new backend module (37 is enough)
- Any legacy `(dashboard)` route revival
- Multi-region infra

---

## 7. Two-week executable MVP sprint plan (post-signoff)

**Assumption:** LLM contract signed, Google Cloud Console access granted, one Design Partner LOI in hand.

**Week 1:**
- D1–D2: Reconcile `feature_ai_copilot` + `AI_HONESTY.md` + `README.md`; sign a new PRC
- D3–D4: Repair `fix/login-and-keys` working tree; land pricing / MSA / DPA drafts to legal
- D5: Enable Railway backup schedule; live-verify
- D6–D7: OAuth staging setup + smoke test

**Week 2:**
- D1–D2: Muhide subset ingestion into `salesos` production for one tenant (post Phase 7 execution for the subset)
- D3: Deprecate legacy `(dashboard)` routes visibly (banner + redirect)
- D4–D5: Provision Stripe live keys; test first invoice
- D6: Public status page + support email live
- D7: Design Partner onboarding session

**Deliverable at end of 2 weeks:** running Design Partner tenant with all 12 DoD criteria addressed or in-flight.

---

*MVP scope — evidence-signed. See `09_PRODUCT_ROADMAP.md` for beyond-MVP horizon.*
