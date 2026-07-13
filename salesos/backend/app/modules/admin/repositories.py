from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .models import (
    AICostRecord,
    FeatureFlag,
    HealthSnapshot,
    Invoice,
    Job,
    License,
    Plan,
    Transaction,
)


class InMemoryPlanRepository:
    def __init__(self):
        self._plans: dict[uuid.UUID, Plan] = {}
        self._seed()

    def _seed(self):
        free = Plan(
            id=uuid.uuid4(), name="Free", tier="free",
            price_monthly=0, price_yearly=0,
            max_users=1, max_storage_mb=100, max_api_calls=1000,
            features=["basic_search", "basic_crm"],
        )
        starter = Plan(
            id=uuid.uuid4(), name="Starter", tier="starter",
            price_monthly=299, price_yearly=2990,
            max_users=5, max_storage_mb=1000, max_api_calls=10000,
            features=["basic_search", "basic_crm", "email_enrichment", "reports"],
        )
        growth = Plan(
            id=uuid.uuid4(), name="Growth", tier="growth",
            price_monthly=999, price_yearly=9990,
            max_users=25, max_storage_mb=10000, max_api_calls=100000,
            features=["advanced_search", "full_crm", "email_enrichment", "ai_scoring", "reports", "api_access"],
        )
        enterprise = Plan(
            id=uuid.uuid4(), name="Enterprise", tier="enterprise",
            price_monthly=4999, price_yearly=49990,
            max_users=999, max_storage_mb=100000, max_api_calls=1000000,
            features=["advanced_search", "full_crm", "email_enrichment", "ai_scoring",
                       "reports", "api_access", "custom_integrations", "dedicated_support", "sso"],
        )
        for p in [free, starter, growth, enterprise]:
            self._plans[p.id] = p

    async def list(self) -> list[Plan]:
        return list(self._plans.values())

    async def get(self, plan_id: uuid.UUID) -> Plan | None:
        return self._plans.get(plan_id)

    async def create(self, plan: Plan) -> Plan:
        now = datetime.now(timezone.utc)
        if plan.is_active is None:
            plan.is_active = True
        if plan.created_at is None:
            plan.created_at = now
        if plan.updated_at is None:
            plan.updated_at = now
        self._plans[plan.id] = plan
        return plan

    async def update(self, plan_id: uuid.UUID, data: dict) -> Plan | None:
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        for key, value in data.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)
        plan.updated_at = datetime.now(timezone.utc)
        return plan


class InMemoryLicenseRepository:
    def __init__(self):
        self._licenses: dict[uuid.UUID, License] = {}

    async def list(self) -> list[License]:
        return list(self._licenses.values())

    async def get(self, license_id: uuid.UUID) -> License | None:
        return self._licenses.get(license_id)

    async def create(self, license: License) -> License:
        now = datetime.now(timezone.utc)
        if license.is_active is None:
            license.is_active = True
        if license.created_at is None:
            license.created_at = now
        if license.updated_at is None:
            license.updated_at = now
        self._licenses[license.id] = license
        return license

    async def find_by_tenant(self, tenant_id: str | uuid.UUID) -> list[License]:
        tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        return [l for l in self._licenses.values() if l.tenant_id == tid]


class InMemoryInvoiceRepository:
    def __init__(self):
        self._invoices: dict[uuid.UUID, Invoice] = {}
        self._transactions: dict[uuid.UUID, Transaction] = {}
        self._seed()

    def _seed(self):
        t1, t2 = uuid.uuid4(), uuid.uuid4()
        now = datetime.now(timezone.utc)
        inv1 = Invoice(id=uuid.uuid4(), tenant_id=t1, amount=299, status="paid",
                       description="Starter Plan - Monthly", due_date=now,
                       paid_at=now - timedelta(days=2))
        inv2 = Invoice(id=uuid.uuid4(), tenant_id=t1, amount=299, status="pending",
                       description="Starter Plan - Monthly", due_date=now + timedelta(days=28))
        inv3 = Invoice(id=uuid.uuid4(), tenant_id=t2, amount=999, status="overdue",
                       description="Growth Plan - Monthly", due_date=now - timedelta(days=5))
        inv4 = Invoice(id=uuid.uuid4(), tenant_id=t2, amount=999, status="paid",
                       description="Growth Plan - Monthly", paid_at=now - timedelta(days=35),
                       due_date=now - timedelta(days=30))
        for inv in [inv1, inv2, inv3, inv4]:
            self._invoices[inv.id] = inv

        tx1 = Transaction(id=uuid.uuid4(), tenant_id=t1, invoice_id=inv1.id,
                          amount=299, status="completed", method="card",
                          reference="TXN-001", description="Starter Plan Payment")
        tx2 = Transaction(id=uuid.uuid4(), tenant_id=t2, invoice_id=inv4.id,
                          amount=999, status="completed", method="bank_transfer",
                          reference="TXN-002", description="Growth Plan Payment")
        self._transactions[tx1.id] = tx1
        self._transactions[tx2.id] = tx2

    async def list_invoices(self, tenant_id: str | None = None) -> list[Invoice]:
        invs = list(self._invoices.values())
        if tenant_id:
            tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
            invs = [i for i in invs if i.tenant_id == tid]
        return sorted(invs, key=lambda x: x.created_at, reverse=True)

    async def list_transactions(self, tenant_id: str | None = None) -> list[Transaction]:
        txs = list(self._transactions.values())
        if tenant_id:
            tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
            txs = [t for t in txs if t.tenant_id == tid]
        return sorted(txs, key=lambda x: x.created_at, reverse=True)


class InMemoryFeatureFlagRepository:
    def __init__(self):
        self._flags: dict[uuid.UUID, FeatureFlag] = {}
        self._seed()

    def _seed(self):
        flags = [
            FeatureFlag(id=uuid.uuid4(), key="ai_copilot", name="AI Copilot",
                        description="Enable AI-powered copilot assistant", enabled=True),
            FeatureFlag(id=uuid.uuid4(), key="advanced_search", name="Advanced Search",
                        description="Enable semantic and hybrid search", enabled=True),
            FeatureFlag(id=uuid.uuid4(), key="crm_kanban", name="CRM Kanban Board",
                        description="Enable Kanban view for CRM pipeline", enabled=False),
            FeatureFlag(id=uuid.uuid4(), key="workflow_automation", name="Workflow Automation",
                        description="Enable automated workflow triggers", enabled=True),
            FeatureFlag(id=uuid.uuid4(), key="sso_enabled", name="SSO Authentication",
                        description="Enable Single Sign-On", enabled=False, is_global=False),
            FeatureFlag(id=uuid.uuid4(), key="export_pdf", name="PDF Export",
                        description="Enable PDF export for reports", enabled=True),
        ]
        for f in flags:
            self._flags[f.id] = f

    async def list(self) -> list[FeatureFlag]:
        return list(self._flags.values())

    async def get(self, flag_id: uuid.UUID) -> FeatureFlag | None:
        return self._flags.get(flag_id)

    async def get_by_key(self, key: str) -> FeatureFlag | None:
        for f in self._flags.values():
            if f.key == key:
                return f
        return None

    async def create(self, flag: FeatureFlag) -> FeatureFlag:
        now = datetime.now(timezone.utc)
        if flag.is_global is None:
            flag.is_global = True
        if flag.created_at is None:
            flag.created_at = now
        if flag.updated_at is None:
            flag.updated_at = now
        self._flags[flag.id] = flag
        return flag

    async def update(self, flag_id: uuid.UUID, data: dict) -> FeatureFlag | None:
        flag = self._flags.get(flag_id)
        if not flag:
            return None
        for key, value in data.items():
            if hasattr(flag, key) and value is not None:
                setattr(flag, key, value)
        flag.updated_at = datetime.now(timezone.utc)
        return flag

    async def set_tenant_override(self, flag_id: uuid.UUID, tenant_id: str, enabled: bool) -> FeatureFlag | None:
        flag = self._flags.get(flag_id)
        if not flag:
            return None
        flag.tenant_overrides[tenant_id] = enabled
        flag.updated_at = datetime.now(timezone.utc)
        return flag

    async def get_tenants_for_flag(self, flag_id: uuid.UUID) -> list[dict]:
        flag = self._flags.get(flag_id)
        if not flag:
            return []
        result = []
        for tid, enabled in flag.tenant_overrides.items():
            result.append({"flag_id": flag_id, "flag_key": flag.key, "tenant_id": tid, "enabled": enabled})
        return result


class InMemoryJobRepository:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._seed()

    def _seed(self):
        now = datetime.now(timezone.utc)
        jobs = [
            Job(id="job-001", type="data_ingestion", status="completed", progress=100,
                tenant_id="tenant-1", payload={"source": "notion", "records": 1500},
                result={"imported": 1500, "errors": 2},
                started_at=now - timedelta(hours=2), completed_at=now - timedelta(hours=1, minutes=45),
                created_at=now - timedelta(hours=2)),
            Job(id="job-002", type="entity_resolution", status="running", progress=65,
                tenant_id="tenant-2", payload={"batch_id": "batch-42"},
                started_at=now - timedelta(minutes=30), created_at=now - timedelta(hours=1)),
            Job(id="job-003", type="email_enrichment", status="failed", progress=42,
                tenant_id="tenant-1", payload={"contacts": 500},
                error_message="Rate limit exceeded on provider API", retry_count=2, max_retries=3,
                started_at=now - timedelta(hours=3), completed_at=now - timedelta(hours=2, minutes=45),
                created_at=now - timedelta(hours=3)),
            Job(id="job-004", type="report_generation", status="pending", progress=0,
                tenant_id="tenant-3", payload={"report_type": "monthly", "period": "2026-06"},
                created_at=now - timedelta(minutes=10)),
            Job(id="job-005", type="sync_crm", status="completed", progress=100,
                tenant_id="tenant-1", payload={"provider": "hubspot"},
                result={"synced": 320, "updated": 45, "errors": 0},
                started_at=now - timedelta(days=1), completed_at=now - timedelta(days=1, hours=-23),
                created_at=now - timedelta(days=1)),
        ]
        for j in jobs:
            j.logs = [
                {"level": "INFO", "message": f"Job {j.id} initialized", "timestamp": (now - timedelta(hours=2)).isoformat()},
                {"level": "INFO", "message": f"Processing with payload: {j.payload}", "timestamp": (now - timedelta(hours=1, minutes=55)).isoformat()},
            ]
            if j.status == "completed":
                j.logs.append({"level": "INFO", "message": "Job completed successfully", "timestamp": now.isoformat()})
            elif j.status == "failed":
                j.logs.append({"level": "ERROR", "message": j.error_message or "Unknown error", "timestamp": now.isoformat()})
            self._jobs[j.id] = j

    async def list(self, status: str | None = None, job_type: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[Job], int]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        if job_type:
            jobs = [j for j in jobs if j.type == job_type]
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        total = len(jobs)
        start = (page - 1) * page_size
        return jobs[start:start + page_size], total

    async def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def retry(self, job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if not job or job.status != "failed":
            return None
        job.status = "pending"
        job.retry_count += 1
        job.error_message = None
        job.result = None
        job.completed_at = None
        job.updated_at = datetime.now(timezone.utc)
        job.logs.append({"level": "INFO", "message": "Retry requested", "timestamp": datetime.now(timezone.utc).isoformat()})
        return job


class InMemoryAICostRepository:
    def __init__(self):
        self._records: list[AICostRecord] = []
        self._seed()

    def _seed(self):
        now = datetime.now(timezone.utc)
        t1, t2 = uuid.uuid4(), uuid.uuid4()
        records = [
            AICostRecord(id=uuid.uuid4(), model="gpt-4o", tenant_id=t1, prompt_tokens=5000, completion_tokens=1200, total_tokens=6200, cost=0.124, operation="completion", created_at=now - timedelta(hours=1)),
            AICostRecord(id=uuid.uuid4(), model="gpt-4o-mini", tenant_id=t1, prompt_tokens=15000, completion_tokens=3000, total_tokens=18000, cost=0.045, operation="completion", created_at=now - timedelta(hours=2)),
            AICostRecord(id=uuid.uuid4(), model="gpt-4o", tenant_id=t2, prompt_tokens=8000, completion_tokens=2000, total_tokens=10000, cost=0.200, operation="completion", created_at=now - timedelta(hours=3)),
            AICostRecord(id=uuid.uuid4(), model="text-embedding-3-large", tenant_id=t1, prompt_tokens=0, completion_tokens=0, total_tokens=50000, cost=0.065, operation="embedding", created_at=now - timedelta(hours=4)),
            AICostRecord(id=uuid.uuid4(), model="gpt-4o", tenant_id=None, prompt_tokens=2000, completion_tokens=500, total_tokens=2500, cost=0.050, operation="completion", created_at=now - timedelta(hours=5)),
        ]
        self._records = records

    async def list(self, model: str | None = None, tenant_id: str | None = None,
                   days: int = 30, page: int = 1, page_size: int = 20) -> tuple[list[AICostRecord], int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        records = [r for r in self._records if r.created_at >= cutoff]
        if model:
            records = [r for r in records if r.model == model]
        if tenant_id:
            tid = uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
            records = [r for r in records if r.tenant_id == tid]
        records.sort(key=lambda x: x.created_at, reverse=True)
        total = len(records)
        start = (page - 1) * page_size
        return records[start:start + page_size], total

    async def get_summary(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = [r for r in self._records if r.created_at >= cutoff]

        total_cost = sum(r.cost for r in recent)
        total_tokens = sum(r.total_tokens for r in recent)

        by_model: dict[str, dict] = {}
        by_tenant: dict[str, dict] = {}
        by_operation: dict[str, dict] = {}

        for r in recent:
            m = by_model.setdefault(r.model, {"model": r.model, "cost": 0, "tokens": 0})
            m["cost"] += r.cost
            m["tokens"] += r.total_tokens

            t = by_tenant.setdefault(str(r.tenant_id) if r.tenant_id else "system", {"tenant_id": str(r.tenant_id) if r.tenant_id else "system", "cost": 0, "tokens": 0})
            t["cost"] += r.cost
            t["tokens"] += r.total_tokens

            o = by_operation.setdefault(r.operation, {"operation": r.operation, "cost": 0, "tokens": 0})
            o["cost"] += r.cost
            o["tokens"] += r.total_tokens

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_model": [{"model": k, "cost": round(v["cost"], 4), "tokens": v["tokens"]} for k, v in sorted(by_model.items(), key=lambda x: -x[1]["cost"])],
            "by_tenant": [{"tenant_id": k, "cost": round(v["cost"], 4), "tokens": v["tokens"]} for k, v in sorted(by_tenant.items(), key=lambda x: -x[1]["cost"])],
            "by_operation": [{"operation": k, "cost": round(v["cost"], 4), "tokens": v["tokens"]} for k, v in sorted(by_operation.items(), key=lambda x: -x[1]["cost"])],
        }

    async def get_usage(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = [r for r in self._records if r.created_at >= cutoff]

        total_prompt = sum(r.prompt_tokens for r in recent)
        total_completion = sum(r.completion_tokens for r in recent)

        by_model: dict[str, dict] = {}
        by_tenant: dict[str, dict] = {}
        for r in recent:
            m = by_model.setdefault(r.model, {"model": r.model, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            m["prompt_tokens"] += r.prompt_tokens
            m["completion_tokens"] += r.completion_tokens
            m["total_tokens"] += r.total_tokens

            t = by_tenant.setdefault(str(r.tenant_id) if r.tenant_id else "system", {"tenant_id": str(r.tenant_id) if r.tenant_id else "system", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            t["prompt_tokens"] += r.prompt_tokens
            t["completion_tokens"] += r.completion_tokens
            t["total_tokens"] += r.total_tokens

        return {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "by_model": list(by_model.values()),
            "by_tenant": list(by_tenant.values()),
        }


class InMemoryHealthRepository:
    def __init__(self):
        self._history: list[HealthSnapshot] = []
        self._start_time = datetime.now(timezone.utc)
        self._seed()

    def _seed(self):
        now = datetime.now(timezone.utc)
        statuses = ["healthy", "healthy", "degraded", "healthy", "healthy", "healthy"]
        for i in range(6):
            ts = now - timedelta(hours=23) + timedelta(hours=4 * i)
            is_degraded = statuses[i] == "degraded"
            self._history.append(HealthSnapshot(
                timestamp=ts,
                overall_status=statuses[i],
                components={
                    "database": "degraded" if is_degraded else "healthy",
                    "cache": "healthy",
                    "graph": "healthy" if not is_degraded else "unhealthy",
                    "kafka": "healthy",
                    "rate_limiter": "healthy",
                },
            ))

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

    async def get_detailed_health(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "overall_status": "healthy",
            "uptime_seconds": self.uptime_seconds,
            "components": [
                {"component": "database", "status": "healthy", "latency_ms": 5.2, "last_check": now, "details": "PostgreSQL 15 — connected, pool: 5/20"},
                {"component": "cache", "status": "healthy", "latency_ms": 1.8, "last_check": now, "details": "Redis 7 — connected, hit rate: 94%"},
                {"component": "graph", "status": "healthy", "latency_ms": 12.5, "last_check": now, "details": "Neo4j 5 — connected, nodes: 45K"},
                {"component": "kafka", "status": "healthy", "latency_ms": 3.1, "last_check": now, "details": "Kafka 3.6 — 4 topics, 12 partitions"},
                {"component": "rate_limiter", "status": "healthy", "latency_ms": 0.3, "last_check": now, "details": "In-memory rate limiter — 60 req/min"},
                {"component": "event_bus", "status": "healthy", "latency_ms": 2.0, "last_check": now, "details": "In-memory event bus — active"},
            ],
        }

    async def get_history(self, hours: int = 24) -> list[HealthSnapshot]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [h for h in self._history if h.timestamp >= cutoff]
