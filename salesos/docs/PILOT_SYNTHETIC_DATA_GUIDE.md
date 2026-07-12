# SalesOS Pilot — Synthetic Data Guide

> دليل البيانات الاصطناعية لبرنامج التجربة الأولية
> How to generate, verify, and manage pilot test data

---

## Overview / نظرة عامة

SalesOS يوفر مولد بيانات اصطناعية مخصص لبرنامج التجربة الأولية. البيانات تتضمن:

- **5 شركات سعودية** — في قطاعات مختلفة (طاقة، اتصالات، مالية، طب، تقنية)
- **13 صانع قرار** — موزعين على الشركات الخمس
- **13 فرصة** — في مراحل مختلفة من خط الأنابيب
- **20 إشارة** — توظيف، عقود، توسع، شراكات، أنظمة
- **13 حدث زمني** — اجتماعات، مكالمات، إيميلات، عروض
- **10 مهام** — مُنشأة من NBA ويدوياً

**الإجمالي: SAR 25.35M في خط الأنابيب**

---

## Step 1: Run pilot-seed.py / تشغيل مولد البيانات

### Method A: Run directly (recommended)

```powershell
# From the project root
python -m backend.demo.pilot_seed
```

### Method B: Via Docker

```powershell
docker compose exec backend python -m backend.demo.pilot_seed
```

### Expected Output

```
============================================================
  SalesOS Pilot Seed Generator
============================================================
  Tenant: pilot_tenant
  Companies: 5

  [OK] 13 decision makers
  [OK] 13 opportunities
  [OK] 20 signals
  [OK] 13 timeline events
  [OK] 10 tasks

  +--------------+------+
  | Metric       | Count|
  +--------------+------+
  | companies    |    5 |
  | decision_makers |  13 |
  | opportunities |   13 |
  | signals      |   20 |
  | timeline     |   13 |
  | tasks        |   10 |
  +--------------+------+

  [FILE] Written to: C:\...\backend\demo\pilot_data.json

  == Gulf Energy Co. (ID: 1) ==
     Industry: energy  |  City: الرياض
     Top Opportunity: فرصة حلول إدارة الطاقة — طاقة الخليج
     Value: SAR 3,500,000  |  Stage: proposing
     Confidence: 72%  |  Buying Intent: 80%

  ...

  [DONE] Pilot data ready. Run .\pilot-onboard.ps1 to verify deployment.
```

### Data File Location

After running, the generated data is saved to:

```
backend/demo/pilot_data.json
```

---

## Step 2: Verify the 5 Companies / التحقق من الشركات

### Via API

```powershell
# Check all companies are loaded
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/companies?tenant_id=pilot_tenant" `
  -ContentType "application/json" | ConvertTo-Json -Depth 5
```

### Expected Companies

| ID | Name (AR) | Name (EN) | Industry | City | CR Number |
|----|-----------|-----------|----------|------|-----------|
| 1 | شركة طاقة الخليج | Gulf Energy Co. | Energy | الرياض | 3010000001 |
| 2 | شركة أثير للاتصالات | Atheer Telecom Co. | Telecom | جدة | 3010000002 |
| 3 | بنك الراجحي المالي | Al Rajhi Financial | Financial | الدمام | 3010000003 |
| 4 | مستشفى السلام الطبي | Al Salam Medical Group | Healthcare | الخبر | 3010000004 |
| 5 | شركة بيانات التقنية | Bayanat Tech Solutions | Technology | الجبيل | 3010000005 |

### Quick Verification Script

```powershell
# Verify all 5 companies exist
$companies = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/companies?tenant_id=pilot_tenant" -ContentType "application/json"
Write-Host "Companies found: $($companies.Count)"
foreach ($c in $companies) {
    Write-Host "  [$($c.id)] $($c.name_en) — $($c.name_ar) ($($c.industry))"
}
```

---

## Step 3: Create Test Users / إنشاء مستخدمين تجريبيين

### Target: 10-15 users across 5 companies

Create users via the Identity API or Identity module:

```powershell
# Example: Create a pilot user
$body = @{
    email = "ahmed.otaibi@gulfenergy.sa"
    password = "SalesOS-Gulf-Manager-001"
    name = "أحمد العتيبي"
    role = "manager"
    tenant_id = "pilot_tenant"
    company_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/identity/users" `
  -Method POST -Body $body -ContentType "application/json"
```

### Recommended User Distribution

| Company | Users | Roles |
|---------|-------|-------|
| Gulf Energy (1) | 3 | 1 Manager + 2 Reps |
| Atheer Telecom (2) | 2 | 1 Manager + 1 Rep |
| Al Rajhi Financial (3) | 3 | 1 Manager + 2 Reps |
| Al Salam Medical (4) | 2 | 1 Manager + 1 Rep |
| Bayanat Tech (5) | 3 | 1 Manager + 2 Reps |
| **Total** | **13** | |

### User Naming Convention

```
Email:    {first}.{last}@{company-domain}.sa
Password: SalesOS-{Company}-{Role}-{###}

Examples:
  ahmed.otaibi@gulfenergy.sa       / SalesOS-Gulf-Manager-001
  sara.ghamdi@gulfenergy.sa        / SalesOS-Gulf-Rep-001
  khalid.almutairi@gulfenergy.sa   / SalesOS-Gulf-Rep-002
  nora.zahrani@atheertelecom.sa    / SalesOS-Atheer-Manager-001
  faisal.alahmadi@atheertelecom.sa / SalesOS-Atheer-Rep-001
  ...
```

### Verify User Creation

```powershell
# List all pilot users
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/identity/users?tenant_id=pilot_tenant" `
  -ContentType "application/json" | ConvertTo-Json -Depth 3
```

---

## Step 4: Generate Sample Data / توليد بيانات تجريبية

### Sample Decisions / عينات قرارات

After users log in and interact with the system, the Decision Engine will generate NBA recommendations. To manually trigger evaluation:

```powershell
# Evaluate NBA for each company
foreach ($cid in 1..5) {
    $body = @{ company_id = $cid; tenant_id = "pilot_tenant" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/decision/evaluate" `
      -Method POST -Body $body -ContentType "application/json"
    Write-Host "Company $cid — Action: $($result.action) | Confidence: $($result.confidence)"
}
```

### Sample Opportunities / عينات الفرص

Opportunities are seeded automatically. Verify via API:

```powershell
$opps = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/opportunities?tenant_id=pilot_tenant" `
  -ContentType "application/json"
Write-Host "Total opportunities: $($opps.Count)"
Write-Host "Total pipeline value: SAR $(($opps | Measure-Object -Property estimated_value -Sum).Sum)"
```

### Sample Tasks / عينات المهام

Tasks are seeded automatically. Verify via API:

```powershell
$tasks = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks?tenant_id=pilot_tenant" `
  -ContentType "application/json"
Write-Host "Total tasks: $($tasks.Count)"
foreach ($t in $tasks) {
    Write-Host "  [$($t.priority)] $($t.title) — $($t.status)"
}
```

---

## Step 5: Verify Monitoring Dashboard / التحقق من لوحة المراقبة

### Check Metrics Endpoint

```powershell
# Decision Engine metrics
$metrics = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/decision/metrics" `
  -ContentType "application/json"

Write-Host "Evaluations:        $($metrics.evaluations)"
Write-Host "Decisions Created:  $($metrics.decisions_created)"
Write-Host "Decisions Accepted: $($metrics.decisions_accepted)"
Write-Host "Avg Eval Time:      $($metrics.avg_eval_ms)ms"
```

### Check Event Runtime

```powershell
$events = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/event-runtime/stats" `
  -ContentType "application/json"

Write-Host "Dead Letter Queue: $($events.dead_letter_count)"
Write-Host "Events Published:  $($events.metrics.events_published)"
Write-Host "Events Processed:  $($events.metrics.events_processed)"
```

### Check Grafana (if enabled)

```
URL: http://localhost:3001
Login: admin / {GRAFANA_PASSWORD from .env.staging}
```

Verify dashboards show:
- API request volume
- Response times
- Error rates (should be 0 or minimal)
- Decision Engine throughput

### Quick Health Check

```powershell
# Run the full verification script
.\scripts\pilot-verify.ps1 -BaseUrl "http://localhost:8000" -TenantId "pilot_tenant"
```

---

## Data Summary / ملخص البيانات

After all steps, your pilot environment should contain:

| Data Type | Count | Source |
|-----------|-------|--------|
| Companies | 5 | pilot_seed.py |
| Decision Makers | 13 | pilot_seed.py |
| Opportunities | 13 | pilot_seed.py |
| Signals | 20 | pilot_seed.py |
| Timeline Events | 13 | pilot_seed.py |
| Tasks | 10 | pilot_seed.py |
| Users | 10-15 | Identity API |
| NBA Evaluations | 5+ | Decision Engine |
| **Total Pipeline** | **SAR 25.35M** | Aggregated |

---

## Troubleshooting / حل المشكلات

### Issue: Seed script fails

```
Error: ModuleNotFoundError: No module named 'backend.demo.pilot_seed'
```

**Solution:** Run from the project root directory:
```powershell
cd C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\salesos
python -m backend.demo.pilot_seed
```

### Issue: API returns 401 Unauthorized

**Solution:** Include the tenant header and/or auth token:
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "X-Tenant-Id" = "pilot_tenant"
    "Authorization" = "Bearer <your-jwt-token>"
}
```

### Issue: No data returned from API

**Solution:** Verify the seed script ran successfully and `pilot_data.json` exists in `backend/demo/`.

### Issue: Companies have Arabic characters garbled

**Solution:** Ensure your terminal supports UTF-8:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

*Last updated: 2026-07-12*
*Version: 1.0 — Pilot Launch*
*Linked: PILOT_LAUNCH_CHECKLIST.md, pilot_seed.py, pilot-onboard.ps1*
