# SalesOS Pilot Launch Checklist

> Practical execution checklist for the Pilot Launch program.
> Owner: Release Manager | Review cadence: Weekly

---

## Pre-Pilot (Week 0)

### Company Selection
- [ ] Select 3-5 pilot companies from existing pipeline (seed_data.py has 37 companies)
- [ ] Prioritize mix: 1 enterprise (Aramco/STC), 1 mid-market (Zamil/Almarai), 1-2 SMB (Arabian Sea IT/Al Rawad)
- [ ] Confirm each company has an active opportunity in the pipeline
- [ ] Identify 10-15 pilot users across companies (role mix: managers + reps)

### User Provisioning
- [ ] Create pilot user accounts in Identity module (`/api/v1/identity`)
- [ ] Assign tenant isolation — each company gets a unique `tenant_id`
- [ ] Verify RBAC permissions for each role (manager vs rep)
- [ ] Distribute login credentials + onboarding guide

### Data Preparation
- [ ] Run `python -m demo.seed_data` to generate baseline data
- [ ] Run `python -m demo.seed_graph` for knowledge graph relationships
- [ ] Verify Company DNA loads for each pilot company
- [ ] Verify signals exist for each pilot company (1-3 per company)
- [ ] Verify opportunities exist in correct pipeline stages
- [ ] Confirm decision makers are linked to companies

### Deployment
- [ ] Deploy backend to staging (FastAPI on `localhost:8000` or staging URL)
- [ ] Deploy frontend to staging (Next.js on `localhost:3000` or staging URL)
- [ ] Verify PostgreSQL is healthy (`/health/ready` returns `database: connected`)
- [ ] Verify Neo4j is connected (`/health` returns `graph: connected`) or gracefully degraded
- [ ] Verify Event Runtime is initialized (`/event-runtime/stats`)
- [ ] Verify Decision Engine is initialized (`/decision/metrics` returns metrics)
- [ ] Configure CORS for staging frontend URL
- [ ] Configure Sentry DSN for error tracking

### Smoke Tests
- [ ] Run `GET /ping` — returns `{"ping": "pong"}`
- [ ] Run `GET /health` — returns status `ok`
- [ ] Run `POST /api/v1/decision/evaluate` for pilot company — returns NBA
- [ ] Run `GET /api/v1/decision/next-best-action?company_id=X` — returns recommendation
- [ ] Login as each pilot user — verify dashboard loads
- [ ] Verify FeedbackWidget renders on dashboard
- [ ] Submit test feedback via FeedbackWidget — verify `pilot.feedback_submitted` event fires

### Pilot Communication
- [ ] Brief pilot users on goals and timeline (4-week sprint)
- [ ] Distribute weekly survey link (Google Form or in-app NPS)
- [ ] Set up Slack/Teams channel for pilot feedback
- [ ] Share onboarding guide (login, key features, feedback process)
- [ ] Confirm pilot contact person per company

---

## Week 1: Onboarding

### Access Verification
- [ ] All 10-15 pilot users can login successfully
- [ ] Each user sees correct tenant-scoped data (no cross-tenant leakage)
- [ ] Dashboard loads for all pilot users
- [ ] Theme/RTL renders correctly for Arabic users

### Feature Verification
- [ ] Company Intelligence loads for each pilot company
  - Company DNA shows correct signals, decision makers, industry context
  - Search finds pilot companies by name (Arabic and English)
- [ ] NBA recommendations appear when evaluating pilot companies
  - `POST /api/v1/decision/evaluate` returns recommendations with confidence > 0.5
  - Accept/reject buttons work correctly
- [ ] Pipeline Intelligence shows opportunities in correct stages
  - Stale opportunity detection triggers for aged deals
  - Priority assignment reflects urgency
- [ ] Timeline events record user actions
  - Session start events appear in timeline
  - Page views tracked via `usePageTracking`

### Metrics Baseline
- [ ] Record initial `GET /decision/metrics` snapshot
  - `evaluations`, `decisions_created`, `decisions_accepted` at zero
- [ ] Record initial `GET /event-runtime/stats` snapshot
- [ ] Record initial NPS baseline (expect neutral — new product)
- [ ] Verify analytics event queue flushes to `/api/v1/analytics/events`

### First Survey
- [ ] Send Week 1 survey to all pilot users
- [ ] Survey questions: login ease, first impression, feature clarity
- [ ] Target response rate: 70%+ (7 of 10 users)

---

## Week 2-3: Active Usage

### Daily Monitoring (run `pilot-metrics.ps1` daily)
- [ ] NBA acceptance rate trending up (target: >40%)
- [ ] Feedback submissions accumulating (target: 3+ per user per week)
- [ ] No increase in error rates (check `/event-runtime/stats` dead letter count)
- [ ] Response times stable (Decision Engine eval < 200ms)
- [ ] No security incidents (check Sentry for auth failures)

### Feature Monitoring
- [ ] NBA recommendations generate for all pilot companies
  - Confidence scores > 0.6 on average
  - Mix of recommendation types (demo, call, outreach, campaign)
- [ ] Feedback submissions include NPS scores (0-10 scale)
- [ ] Time to Insight: users find relevant company info within 60 seconds
- [ ] Search returns relevant results for Arabic queries
- [ ] Signal types reflect realistic Saudi market activity

### Performance Monitoring
- [ ] Database queries complete in < 100ms (check `/health` response time)
- [ ] Vector search returns results in < 500ms
- [ ] Neo4j graph queries complete in < 200ms (if available)
- [ ] Frontend loads in < 2s on staging
- [ ] No memory leaks in long-running sessions

### Weekly Survey
- [ ] Send Week 2 survey — focus on daily usage patterns
- [ ] Send Week 3 survey — focus on value perception
- [ ] Track NPS trend: expect 5+ point improvement from Week 1
- [ ] Collect qualitative feedback on pain points

### Revenue Impact Tracking
- [ ] Log `outcome_value` on feedback for accepted recommendations
- [ ] Track which recommendations lead to opportunity progression
- [ ] Monitor pipeline value changes for pilot companies
- [ ] Record any deals attributed to NBA recommendations

---

## Week 4: Evaluation

### Final Data Collection
- [ ] Run `pilot-metrics.ps1` for final snapshot
- [ ] Export all decision feedback (`/decisions/history` for each pilot company)
- [ ] Export all analytics events for the 4-week period
- [ ] Collect all survey responses

### Metrics Calculation
- [ ] **NPS Score**: Calculate from FeedbackWidget NPS responses
  - Promoters (9-10), Passives (7-8), Detractors (0-6)
  - NPS = % Promoters - % Detractors
  - Target: NPS > 30 (good), > 50 (excellent)
- [ ] **Time to Value**: Measure from first login to first meaningful action
  - Track via `pilot.session_started` events with page metadata
  - Target: < 5 minutes for first company DNA view
- [ ] **Acceptance Rate**: From Decision Engine metrics
  - `decisions_accepted / decisions_created`
  - Target: > 40%
- [ ] **Feedback Quality**: Average feedback length, NPS distribution
- [ ] **Revenue Impact**: Sum of `outcome_value` from feedback submissions
- [ ] **Error Rate**: Dead letter queue growth over 4 weeks
- [ ] **Feature Adoption**: Which features used most (from widget tracking)

### Pilot Report
- [ ] Compile executive summary with key metrics
- [ ] Include NPS trend chart (Week 1 → Week 4)
- [ ] Include acceptance rate trend chart
- [ ] Include top feedback themes (qualitative)
- [ ] Include revenue impact estimates
- [ ] Include technical issues encountered and resolved
- [ ] Include recommendations for GA launch

### Decision Meeting
- [ ] Present findings to stakeholders
- [ ] Decision matrix:
  - **Proceed to GA**: NPS > 30, acceptance > 40%, no critical bugs
  - **Iterate**: NPS 10-30 or acceptance 20-40%, minor issues
  - **Pivot**: NPS < 10 or acceptance < 20%, fundamental issues
- [ ] Document decision and rationale
- [ ] If proceeding: draft GA launch timeline
- [ ] If iterating: create Sprint 2 backlog from pilot feedback

---

## Rollback Plan

If critical issues are found during the pilot:

1. **Data Issues**: Restore from PostgreSQL backup (`pg_dump` before pilot)
2. **Auth Issues**: Disable pilot user accounts in Identity module
3. **Performance Issues**: Revert to pre-pilot deployment
4. **Security Issues**: Rotate all pilot credentials, audit access logs

---

## Contacts

| Role | Name | Channel |
|------|------|---------|
| Release Manager | TBD | #pilot-launch |
| Backend Lead | TBD | #pilot-launch |
| Frontend Lead | TBD | #pilot-launch |
| Pilot Champion (Company 1) | TBD | Direct message |
| Pilot Champion (Company 2) | TBD | Direct message |

---

*Created: 2026-07-10*
*Linked: PILOT_LAUNCH.md, pilot-metrics.ps1*
