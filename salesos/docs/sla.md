# SalesOS Service Level Agreement (SLA)

**Effective Date:** 2026-07-12
**Version:** 1.0
**Document Owner:** RATL Technology Ltd

---

## 1. Service Overview

SalesOS is a multi-tenant CRM and sales intelligence platform providing:

- **Company Intelligence** — company data, enrichment, entity resolution
- **Hybrid Search** — full-text and semantic search with RRF fusion
- **NBA Decision Platform** — scoring engine, decision provider, workflow automation
- **AI Agents Engine** — prompt registry, AI-assisted insights
- **Dashboard & Analytics** — real-time KPIs, activity tracking, employee intelligence
- **Workflow Automation** — task orchestration, triggers, business process management

The service is delivered as a cloud-hosted SaaS application via Docker Compose orchestration on dedicated infrastructure.

---

## 2. Service Level Commitments

### 2.1 Availability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Monthly Uptime | ≥ 99.9% | Measured per calendar month |
| Maximum Downtime | ≤ 43.8 minutes/week | Excluding scheduled maintenance |
| Planned Maintenance | ≤ 4 hours/month | During designated maintenance windows |

Availability is calculated as:

```
Availability % = ((Total Minutes - Downtime Minutes) / Total Minutes) × 100
```

Downtime is defined as any period where the SalesOS API is unable to process requests due to a platform-side issue. Downtime excludes scheduled maintenance windows, force majeure events, and customer-caused outages.

### 2.2 API Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p50) | < 100ms | Rolling 30-day average |
| API Response Time (p95) | < 500ms | Rolling 30-day average |
| API Response Time (p99) | < 2,000ms | Rolling 30-day average |
| Search Response Time (p95) | < 1,000ms | Rolling 30-day average |
| Search Response Time (p99) | < 3,000ms | Rolling 30-day average |

### 2.3 Data Durability

| Metric | Target |
|--------|--------|
| Data Durability | 99.999% (five nines) |
| Backup Frequency | Daily (automated), Weekly (full snapshot) |
| Backup Retention | 30 days |
| Recovery Point Objective (RPO) | < 24 hours |
| Recovery Time Objective (RTO) | < 4 hours |

---

## 3. Support Levels

### 3.1 Severity Definitions

| Severity | Description | Examples |
|----------|-------------|----------|
| **P0 — Critical** | System is down or data loss has occurred | Total service outage, database corruption, security breach, data loss event |
| **P1 — High** | Major feature is broken, no workaround available | Search returning errors, AI agents failing, dashboard not loading, authentication failures |
| **P2 — Medium** | Minor feature issue, workaround exists | Slow page load, intermittent API errors, cosmetic data inconsistency |
| **P3 — Low** | Cosmetic issue, feature request, or general question | UI alignment, documentation question, enhancement request |

### 3.2 Response Times

| Severity | First Response | Resolution Target | Support Hours |
|----------|---------------|-------------------|---------------|
| P0 — Critical | 15 minutes | 4 hours | 24/7/365 |
| P1 — High | 1 hour | 8 business hours | Sun–Thu, 09:00–17:00 AST |
| P2 — Medium | 4 business hours | 3 business days | Sun–Thu, 09:00–17:00 AST |
| P3 — Low | 24 business hours | 10 business days | Sun–Thu, 09:00–17:00 AST |

### 3.3 Escalation Path

| Level | Trigger | Contact |
|-------|---------|---------|
| L1 — Support | Initial ticket | support@salesos.example.com |
| L2 — Engineering | P0 not resolved in 30 min, P1 not resolved in 4 hrs | engineering@salesos.example.com |
| L3 — Management | P0 not resolved in 2 hrs, P1 not resolved in 8 hrs | management@salesos.example.com |

---

## 4. Exclusions

The following are excluded from SLA calculations and credit eligibility:

### 4.1 Scheduled Maintenance

- Scheduled maintenance windows are excluded from downtime calculations
- Maintenance is performed during **Sunday 02:00–04:00 AST**
- Customers receive notification at least **48 hours** in advance
- Emergency maintenance may be performed with **4 hours** notice

### 4.2 Force Majeure

Events beyond reasonable control, including but not limited to:

- Natural disasters (earthquake, flood, hurricane)
- War, terrorism, civil unrest
- Government action or regulation
- Internet service provider failures
- Third-party cloud provider outages (AWS, Azure, GCP regional outages)

### 4.3 Customer-Caused Issues

- Exceeding agreed-upon rate limits or usage quotas
- Misuse, abuse, or unauthorized use of the platform
- Customer-initiated configuration changes that cause outages
- Customer network or infrastructure issues
- Customer code or integrations that cause service degradation

### 4.4 Beta and Preview Features

- Features marked as "Beta" or "Preview" are not covered by this SLA
- Performance targets do not apply to beta endpoints

---

## 5. Service Credits

### 5.1 Credit Schedule

If SalesOS fails to meet the uptime commitment in a given month, the customer is eligible for the following service credits:

| Monthly Uptime | Credit (% of Monthly Fee) |
|----------------|---------------------------|
| 99.0% – 99.9% | 10% |
| 95.0% – 99.0% | 25% |
| 90.0% – 95.0% | 50% |
| < 90.0% | 100% |

### 5.2 Credit Conditions

- Credits apply only to the monthly subscription fee for the affected service
- Credits are applied to the **next billing cycle**
- Total cumulative credits in any billing period shall not exceed **100% of the monthly fee**
- Credits must be requested within **30 days** of the incident
- Credits are non-transferable and have no cash value

### 5.3 Credit Request Process

1. Customer contacts support within 30 days of the incident
2. Customer provides incident details (date, time, duration, impact)
3. SalesOS verifies the incident against platform monitoring data
4. Credit is applied to the customer's next invoice
5. Customer receives written confirmation of the credit

---

## 6. Reporting and Measurement

### 6.1 SLA Monitoring

SalesOS maintains continuous monitoring of all SLA metrics:

- **Uptime:** Real-time health checks (every 60 seconds) on all production endpoints
- **API Response Times:** Continuous latency monitoring via Prometheus metrics
- **Search Performance:** Dedicated search latency tracking with percentile aggregation
- **Error Rates:** HTTP 5xx error rate tracking per endpoint

### 6.2 Monthly SLA Reports

Customers receive a monthly SLA compliance report containing:

- Uptime percentage for the month
- Response time percentiles (p50, p95, p99)
- Search performance metrics
- Incidents and their resolution times
- Scheduled maintenance windows executed
- Comparison against SLA targets

Reports are delivered by the **5th of each month** for the preceding month.

### 6.3 Real-Time Status

- Status page: `https://status.salesos.example.com`
- Incidents are published in real-time during ongoing events
- Post-incident reports are published within **48 hours** of resolution for P0/P1 incidents

### 6.4 Measurement Disputes

If the customer disputes an SLA measurement:

1. The customer submits a written dispute within **30 days** of receiving the monthly report
2. SalesOS provides raw monitoring data for the disputed period
3. Both parties work in good faith to resolve the discrepancy
4. Unresolved disputes are escalated to management for final determination

---

## 7. Maintenance Windows

### 7.1 Scheduled Maintenance

| Parameter | Value |
|-----------|-------|
| Window | Sunday 02:00–04:00 AST |
| Frequency | Weekly (or as needed) |
| Notice Period | 48 hours minimum |
| Notification Method | Email + Status Page |

### 7.2 Emergency Maintenance

| Parameter | Value |
|-----------|-------|
| Notice Period | 4 hours minimum (when feasible) |
| Notification Method | Email + Status Page + SMS (for P0 issues) |
| Scope | Critical security patches, data integrity fixes |

### 7.3 Maintenance Communication

All maintenance communications include:

- Date and time of maintenance (with time zone)
- Expected duration
- Services affected
- Reason for maintenance
- Impact on service availability
- Contact information for questions

---

## 8. Data Protection and Security

| Requirement | Standard |
|-------------|----------|
| Data Encryption at Rest | AES-256 |
| Data Encryption in Transit | TLS 1.3 |
| Authentication | JWT with refresh token rotation |
| Authorization | Role-Based Access Control (RBAC) |
| Audit Logging | All data access logged with user, timestamp, action |
| Data Residency | Saudi Arabia (KSA PDPL compliant) |
| Data Retention | Maximum 7 years, configurable per tenant |
| Right to Deletion | Supported via tenant admin panel |

---

## 9. General Terms

### 9.1 Amendment

This SLA may be updated with **30 days** written notice to customers. Continued use of the service after the effective date constitutes acceptance.

### 9.2 Termination for SLA Failure

If SalesOS fails to meet the 99.0% uptime target for **three consecutive months**, the customer may terminate their subscription without penalty and receive a prorated refund for the unused portion of the current billing period.

### 9.3 Governing Law

This agreement is governed by the laws of the Kingdom of Saudi Arabia.

### 9.4 Contact

For SLA-related inquiries:

- **Email:** sla@salesos.example.com
- **Support Portal:** https://support.salesos.example.com
- **Phone (P0 only):** +966-XX-XXX-XXXX

---

*Last updated: 2026-07-12*
*Document version: 1.0*
