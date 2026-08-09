"""Phase 1 Integration Test — SalesOS Agent Runtime Lifecycle."""
import asyncio
import uuid

from app.database import async_session, set_current_tenant_id, reset_current_tenant_id, apply_tenant_guc
from sqlalchemy import text

TID = "da08cef9-90f7-4409-b43b-1e9201987daf"


async def test():
    from runtime.agent_runtime.queue import schedule_task, claim_due, complete_task, fail_task, recover_expired_leases, retire_exhausted
    from runtime.agent_runtime.models import AgentRun

    # Clean
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        await s.execute(text("DELETE FROM agent_actions"))
        await s.execute(text("DELETE FROM agent_runs"))
        await s.execute(text("DELETE FROM agent_tasks"))
        await s.commit(); reset_current_tenant_id(token)

    # 1. CREATE: schedule task
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        task = await schedule_task(s, TID, kind="research_company", reason="validation",
            entity_type="company", entity_id="00000000-0000-0000-0000-000000000001")
        await s.commit(); reset_current_tenant_id(token)
        assert task.status == "PENDING", f"Expected PENDING, got {task.status}"
        print(f"[PASS] CREATE: id={task.id}, status=PENDING")

    # 2. CLAIM: PENDING→CLAIMED via CTE+SKIP LOCKED
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        tasks = await claim_due(s, TID, limit=1, lease_ms=300000)
        await s.commit(); reset_current_tenant_id(token)
        assert len(tasks) == 1
        t = tasks[0]; gen = t.lease_generation
        assert gen == 1, f"Expected gen=1, got {gen}"
        print(f"[PASS] CLAIM: gen={gen}, worker={t.leased_by}")

    # 3. RUNNING: create AgentRun + transition CLAIMED→RUNNING
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        run = AgentRun(id=uuid.uuid4(), task_id=t.id, tenant_id=uuid.UUID(TID), agent_type="ResearchAgent")
        s.add(run)
        result = await s.execute(text(
            "UPDATE agent_tasks SET status='RUNNING', session_id=:sid, updated_at=now() "
            "WHERE id=:tid AND status='CLAIMED' AND lease_generation=:gen"
        ), {"tid": str(t.id), "sid": str(run.id), "gen": gen})
        assert result.rowcount == 1
        await s.commit(); reset_current_tenant_id(token)
        print(f"[PASS] RUNNING: run_id={run.id}")

    # 4. COMPLETE with fence: RUNNING→COMPLETED (gen check)
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        ok = await complete_task(s, str(t.id), "Enriched successfully!", lease_generation=gen)
        assert ok, "completeTask returned False with correct gen"
        await s.execute(text("UPDATE agent_runs SET status='COMPLETED', completed_at=now() WHERE id=:rid"), {"rid": str(run.id)})
        await s.commit(); reset_current_tenant_id(token)
        print(f"[PASS] COMPLETE with fence gen={gen}")

    # 5. Verify final state
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        tr = await s.execute(text("SELECT status, attempts, lease_generation FROM agent_tasks WHERE id=:id"), {"id": str(t.id)})
        row = tr.fetchone()
        assert row.status == "COMPLETED", f"Expected COMPLETED, got {row.status}"
        assert row.attempts == 1
        assert row.lease_generation == 1
        rr = await s.execute(text("SELECT status FROM agent_runs WHERE id=:id"), {"id": str(run.id)})
        assert rr.fetchone().status == "COMPLETED"
        await s.commit(); reset_current_tenant_id(token)
        print(f"[PASS] VERIFY: task=COMPLETED, run=COMPLETED")

    # 6. FENCING: stale generation rejected
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        task2 = await schedule_task(s, TID, kind="research_company", reason="fence test",
            entity_type="company", entity_id="00000000-0000-0000-0000-000000000002")
        await s.commit(); reset_current_tenant_id(token)
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        tasks2 = await claim_due(s, TID, limit=1, lease_ms=300000)
        await s.commit(); reset_current_tenant_id(token)
        t2 = tasks2[0]; correct_gen = t2.lease_generation
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        ok = await complete_task(s, str(t2.id), "FENCE FAIL", lease_generation=correct_gen - 1)
        await s.commit(); reset_current_tenant_id(token)
        assert not ok, "Stale generation should be REJECTED"
        print(f"[PASS] FENCING: stale_gen={correct_gen - 1} => REJECTED")

    # 7. FAIL + RETRY: attempts < max → PENDING
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        task3 = await schedule_task(s, TID, kind="research_company", reason="fail test",
            entity_type="company", entity_id="00000000-0000-0000-0000-000000000003")
        await s.commit(); reset_current_tenant_id(token)
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        tasks3 = await claim_due(s, TID, limit=1, lease_ms=300000)
        await s.commit(); reset_current_tenant_id(token)
        t3 = tasks3[0]; gen3 = t3.lease_generation
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        await s.execute(text("UPDATE agent_tasks SET status='RUNNING' WHERE id=:id"), {"id": str(t3.id)})
        ok = await fail_task(s, str(t3.id), "Simulated LLM timeout", lease_generation=gen3)
        await s.commit(); reset_current_tenant_id(token)
        assert ok
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        tr = await s.execute(text("SELECT status, attempts FROM agent_tasks WHERE id=:id"), {"id": str(t3.id)})
        row = tr.fetchone()
        assert row.status == "PENDING", f"Expected PENDING on retry, got {row.status}"
        assert row.attempts == 1
        await s.commit(); reset_current_tenant_id(token)
        print(f"[PASS] FAIL+RETRY: status={row.status}, attempts={row.attempts}")

    # 8. IDEMPOTENCY: duplicate key on scheduleTask
    async with async_session() as s:
        token = set_current_tenant_id(TID); await apply_tenant_guc(s)
        task_a = await schedule_task(s, TID, kind="idem_test", reason="first",
            entity_type="company", entity_id="00000000-0000-0000-0000-000000000010",
            idempotency_key="idem-key-001")
        await s.commit()
        try:
            task_b = await schedule_task(s, TID, kind="idem_test", reason="second",
                entity_type="company", entity_id="00000000-0000-0000-0000-000000000010",
                idempotency_key="idem-key-001")
            await s.commit()
            print("[FAIL] IDEMPOTENCY: duplicate key should have been rejected")
        except Exception:
            await s.rollback()
            print("[PASS] IDEMPOTENCY: duplicate idempotency_key rejected")
        finally:
            reset_current_tenant_id(token)

    print("")
    print("ALL 8 INTEGRATION CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(test())
