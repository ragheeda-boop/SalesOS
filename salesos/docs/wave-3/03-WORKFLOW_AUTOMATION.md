# Workflow Automation Architecture

> **الهدف:** تصميم محرك Workflow لأتمتة دورات المبيعات المتكررة
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Sprint 12

---

## 1. Design Philosophy

### المبادئ

1. **Workflow = DAG of Actions** — كل workflow هو Directed Acyclic Graph من الخطوات
2. **Declarative > Imperative** — المستخدم يصف "ماذا" وليس "كيف"
3. **Observable by Default** — كل خطوة تسجل execution trace
4. **Fail Gracefully** — الفشل لا يوقف الـ workflow بالكامل
5. **Template-First** — 80% من workflows تبدأ من قالب

### In Scope vs Out of Scope

| In Scope | Out of Scope |
|----------|-------------|
| Linear + branch workflows | Complex BPMN (sub-processes, multi-instance) |
| Event, schedule, manual triggers | Real-time collaborative editing |
| Email, CRM, Task, Webhook actions | External system orchestration (ERP, HR) |
| Visual drag-and-drop builder | Code-based workflow definitions |
| Execution monitoring + failure alerts | Workflow simulation / what-if analysis |

---

## 2. Workflow Engine Design

### State Machine / DAG Model

```
Workflow
  │
  ├── Trigger (event / schedule / manual)
  ├── Steps (DAG of actions)
  │     │
  │     ├── Action (email, crm, task, webhook, nba, delay, condition)
  │     ├── Branch (if/else condition)
  │     └── Parallel (fan-out / fan-in)
  │
  ├── State (running, paused, completed, failed, cancelled)
  ├── Trace (execution log per step)
  └── SLA (timeout, escalation)
```

### Core Data Model

```typescript
// contracts/workflow/workflow.ts

export interface Workflow {
  id: string
  tenantId: string
  name: string
  description: string
  trigger: WorkflowTrigger
  steps: WorkflowStep[]
  state: WorkflowState
  version: number
  createdBy: string
  createdAt: string
  updatedAt: string
}

export type WorkflowState = 'draft' | 'active' | 'paused' | 'archived'

export interface WorkflowTrigger {
  type: 'event' | 'schedule' | 'manual'
  config: EventTriggerConfig | ScheduleTriggerConfig | ManualTriggerConfig
}

export interface EventTriggerConfig {
  eventType: string        // e.g., "opportunity.stage_changed"
  filter?: DomainFilter    // Optional conditions
}

export interface ScheduleTriggerConfig {
  cron: string             // e.g., "0 9 * * 1" (every Monday 9am)
  timezone: string         // e.g., "Asia/Riyadh"
}

export interface ManualTriggerConfig {
  entityType: string       // e.g., "opportunity"
  label: string            // e.g., "Run Onboarding"
}

export interface WorkflowStep {
  id: string
  type: 'action' | 'branch' | 'parallel'
  label: string
  config: ActionConfig | BranchConfig | ParallelConfig
  nextOnSuccess?: string[]   // Step IDs to run next
  nextOnFailure?: string[]   // Fallback steps
  timeout?: number            // Max execution time (seconds)
  retryPolicy?: RetryPolicy
}

export interface ActionConfig {
  actionType: 'send_email' | 'update_crm' | 'create_task' | 'trigger_nba' | 'webhook' | 'delay' | 'update_opportunity'
  params: Record<string, unknown>
}

export interface BranchConfig {
  condition: ConditionExpression
  trueStepId: string
  falseStepId: string
}

export interface ParallelConfig {
  branches: ParallelBranch[]
  joinType: 'all' | 'any'   // Wait for all or any branch to complete
}

export interface ConditionExpression {
  field: string              // e.g., "opportunity.value"
  operator: '>' | '<' | '==' | '>=' | '<=' | 'contains' | 'in'
  value: unknown
}
```

### Workflow Execution State

```typescript
export interface WorkflowExecution {
  id: string
  workflowId: string
  tenantId: string
  trigger: string
  context: ExecutionContext     // Entity context (opportunity, company)
  state: ExecutionState
  stepExecutions: StepExecution[]
  startedAt: string
  completedAt?: string
  error?: string
}

export type ExecutionState = 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'

export interface StepExecution {
  stepId: string
  state: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  input: Record<string, unknown>
  output?: Record<string, unknown>
  error?: string
  startedAt?: string
  completedAt?: string
  durationMs?: number
}
```

---

## 3. Workflow Engine (Backend)

### Architecture

```python
class WorkflowEngine:
    """Core workflow execution engine."""

    def __init__(self, action_registry: ActionRegistry, event_bus: EventBus):
        self.actions = action_registry
        self.event_bus = event_bus

    async def execute(self, workflow: Workflow, context: ExecutionContext) -> WorkflowExecution:
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            tenant_id=context.tenant_id,
            trigger=context.trigger_type,
            context=context,
            state='running',
        )

        # Resolve entry points (steps with no dependencies)
        entry_points = self._resolve_entry_points(workflow.steps)

        # Execute DAG with topological ordering
        try:
            for step in self._topological_sort(workflow.steps, entry_points):
                step_exec = await self._execute_step(step, execution, context)
                execution.step_executions.append(step_exec)

                if step_exec.state == 'failed':
                    if step.next_on_failure:
                        # Continue with fallback path
                        continue
                    else:
                        execution.state = 'failed'
                        execution.error = step_exec.error
                        break

            if execution.state != 'failed':
                execution.state = 'completed'

        except Exception as e:
            execution.state = 'failed'
            execution.error = str(e)

        execution.completed_at = datetime.utcnow().isoformat()
        await self._record_execution(execution)
        await self._emit_completion_event(execution)
        return execution

    async def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution, context: ExecutionContext) -> StepExecution:
        step_exec = StepExecution(step_id=step.id, state='running', started_at=datetime.utcnow().isoformat())

        try:
            if step.type == 'action':
                action = self.actions.get(step.config.action_type)
                step_exec.output = await action.execute(step.config.params, context)
                step_exec.state = 'completed'

            elif step.type == 'branch':
                result = self._evaluate_condition(step.config.condition, context)
                step_exec.output = {'condition_result': result}
                step_exec.state = 'completed'
                # Routing handled by engine based on result

            elif step.type == 'parallel':
                results = await asyncio.gather(
                    *[self._execute_branch(b, context) for b in step.config.branches]
                )
                step_exec.output = {'branch_results': results}
                step_exec.state = 'completed'

        except Exception as e:
            step_exec.state = 'failed'
            step_exec.error = str(e)
            if step.retry_policy:
                # Retry logic here
                pass

        step_exec.completed_at = datetime.utcnow().isoformat()
        step_exec.duration_ms = self._duration_ms(step_exec.started_at, step_exec.completed_at)
        return step_exec
```

### Action Registry

```python
class ActionRegistry:
    """Registry of all available workflow actions."""

    def __init__(self):
        self._actions: dict[str, Action] = {}

    def register(self, action: Action):
        self._actions[action.type] = action

    def get(self, action_type: str) -> Action:
        action = self._actions.get(action_type)
        if not action:
            raise ValueError(f"Unknown action type: {action_type}")
        return action


class Action(ABC):
    """Base class for workflow actions."""

    @property
    @abstractmethod
    def type(self) -> str: ...

    @abstractmethod
    async def execute(self, params: dict, context: ExecutionContext) -> dict: ...


class SendEmailAction(Action):
    type = "send_email"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Send email via Email Intelligence service."""
        email_service = EmailService()
        result = await email_service.send(
            to=params['to'],
            subject=self._render_template(params['subject_template'], context),
            body=self._render_template(params['body_template'], context),
            opportunity_id=context.entity_id,
        )
        return {"email_id": result.id, "status": result.status}


class UpdateCRMAction(Action):
    type = "update_crm"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Update opportunity stage or field in CRM."""
        crm = CRMModule()
        result = await crm.update_opportunity(
            opportunity_id=context.entity_id,
            updates=params['fields'],
        )
        return {"opportunity_id": result.id, "updated_fields": list(params['fields'].keys())}


class CreateTaskAction(Action):
    type = "create_task"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Create task in Task module."""
        task_service = TaskService()
        task = await task_service.create(
            opportunity_id=context.entity_id,
            title=params['title'],
            description=params.get('description', ''),
            assignee=params['assignee'],
            due_in_days=params.get('due_in_days', 1),
            source='workflow',
        )
        return {"task_id": task.id}


class TriggerNBAAction(Action):
    type = "trigger_nba"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Trigger NBA refresh for an opportunity."""
        nba_service = NBAService()
        nba = await nba_service.recompute(context.entity_id)
        return {"nba_id": nba.id, "action": nba.action}


class WebhookAction(Action):
    type = "webhook"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Call external webhook."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                params['url'],
                json=self._build_payload(params, context),
                headers=params.get('headers', {}),
                timeout=30,
            )
            response.raise_for_status()
            return {"status_code": response.status_code, "body": response.json()}


class DelayAction(Action):
    type = "delay"

    async def execute(self, params: dict, context: ExecutionContext) -> dict:
        """Wait before proceeding."""
        seconds = params.get('seconds', params.get('minutes', 0) * 60)
        await asyncio.sleep(seconds)
        return {"delayed_seconds": seconds}
```

---

## 4. Trigger System

### Trigger Architecture

```
External Events (Kafka)
      │
      ├── opportunity.stage_changed ──────► Check event filter → Start workflow
      ├── opportunity.created ────────────► Start onboarding workflow
      ├── deal_health.changed ────────────► Check health severity → Start escalation
      ├── signal.detected ────────────────► Check signal type → Start follow-up
      └── activity.logged ────────────────► Check activity type → Start nurture
      
Scheduled (Cron)
      │
      ├── Daily 9am ──────────────────────► Check idle opportunities → Start follow-up
      ├── Weekly Monday ──────────────────► Run pipeline health check
      └── Monthly 1st ────────────────────► Generate revenue report
      
Manual (User Click)
      │
      └── "Run Workflow" button ──────────► Start workflow with current entity
```

### Trigger Resolver

```python
class TriggerResolver:
    """Matches incoming events/schedules to workflows."""

    async def match_event(self, event: DomainEvent) -> list[Workflow]:
        """Find all workflows triggered by this event."""
        workflows = await self.store.get_active_workflows_by_trigger('event')
        matched = []

        for wf in workflows:
            config = wf.trigger.config
            if config.event_type == event.type:
                if config.filter:
                    if self._matches_filter(event.data, config.filter):
                        matched.append(wf)
                else:
                    matched.append(wf)

        return matched

    async def match_schedule(self, now: datetime) -> list[tuple[Workflow, list[str]]]:
        """Find all workflows scheduled to run now. Returns (workflow, entity_ids)."""
        workflows = await self.store.get_active_workflows_by_trigger('schedule')
        matched = []

        for wf in workflows:
            config = wf.trigger.config
            if self._cron_matches(config.cron, now, config.timezone):
                entities = await self._resolve_schedule_entities(wf)
                if entities:
                    matched.append((wf, entities))

        return matched
```

---

## 5. Visual Workflow Builder (Frontend)

### Component Architecture

```
WorkflowBuilder
  │
  ├── Canvas (Drag-and-drop DAG editor)
  │     ├── StepNode (action/branch/parallel)
  │     ├── ConnectionLine (step → step)
  │     ├── DropZone (add new step)
  │     └── Minimap (overview of large workflows)
  │
  ├── Toolbar
  │     ├── Actions Palette (available actions)
  │     ├── Templates (load pre-built workflows)
  │     ├── Validate (check workflow consistency)
  │     └── Publish (activate workflow)
  │
  ├── Properties Panel
  │     ├── Step Configuration (params per action type)
  │     ├── Trigger Configuration (event/schedule/manual)
  │     ├── Condition Editor (if/else builder)
  │     └── SLA Settings (timeout, retry, escalation)
  │
  └── Execution Panel
        ├── Recent Executions (live feed)
        ├── Execution Trace (step-by-step log)
        └── Failure Analysis (errors + suggested fixes)
```

### WorkflowBuilder Component

```typescript
// frontend/src/workflow-builder/WorkflowBuilder.tsx

interface WorkflowBuilderProps {
  initialWorkflow?: Workflow
  onSave: (workflow: WorkflowDefinition) => void
}

export function WorkflowBuilder({ initialWorkflow, onSave }: WorkflowBuilderProps) {
  return (
    <WorkflowProvider initialWorkflow={initialWorkflow}>
      <div className="workflow-builder">
        <WorkflowToolbar />
        <div className="workflow-builder__main">
          <ActionPalette />
          <WorkflowCanvas />
          <PropertiesPanel />
        </div>
        <ExecutionPanel />
      </div>
    </WorkflowProvider>
  );
}
```

### Template Selector

| Template | Trigger | Steps | Use Case |
|----------|---------|-------|----------|
| **Follow-Up Sequence** | Event: `deal_health.stagnation` | Delay 1d → Send Email → Create Task → Delay 3d → Send Email | Auto-follow-up on idle deals |
| **Lead Nurturing** | Event: `opportunity.created` | Send Intro Email → Delay 2d → Create Task → Delay 5d → Check Engagement → Branch | Nurture new leads |
| **Deal Escalation** | Event: `deal_health.critical` | Update CRM → Send Alert Email → Create Urgent Task → Notify Manager | Escalate at-risk deals |
| **Onboarding** | Manual: "Start Onboarding" | Send Welcome Email → Create Task List → Delay 7d → Check Progress → Send Reminder | Customer onboarding |
| **Renewal Reminder** | Schedule: 90d before expiry | Check Status → Send Reminder Email → Delay 30d → Send Final Reminder → Escalate | Contract renewal |

---

## 6. Monitoring & Execution Traces

### Execution Trace Data Model

```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL REFERENCES workflows(id),
    tenant_id UUID NOT NULL,
    trigger_type VARCHAR(20) NOT NULL,      -- event / schedule / manual
    trigger_detail VARCHAR(255),
    entity_type VARCHAR(50),                 -- opportunity / company
    entity_id UUID,
    state VARCHAR(20) NOT NULL,              -- running / completed / failed / cancelled
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    error TEXT,
    total_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_step_executions (
    id UUID PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES workflow_executions(id),
    step_id VARCHAR(100) NOT NULL,
    step_type VARCHAR(20) NOT NULL,          -- action / branch / parallel
    action_type VARCHAR(50),                 -- send_email / update_crm / etc.
    state VARCHAR(20) NOT NULL,
    input JSONB,
    output JSONB,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER
);
```

### Monitoring Dashboard

```
Workflow Monitoring
│
├── Overview
│   ├── Active Workflows: 47
│   ├── Success Rate: 94.2% (24h)
│   ├── Avg Duration: 3.2s
│   └── Failed Today: 3
│
├── Active Executions (Live)
│   ├── opp_abc — "Follow-Up Sequence" — Step 3/5 — running 2m
│   ├── comp_xyz — "Deal Escalation" — Step 2/4 — running 30s
│   └── opp_def — "Lead Nurturing" — Step 1/6 — error (retrying)
│
├── Failure Analysis
│   ├── common errors (last 7 days)
│   │   ├── Email send failed: 12 (30%)
│   │   ├── Webhook timeout: 8 (20%)
│   │   └── CRM update rejected: 5 (12%)
│   └── Suggested fixes
│
└── SLA Compliance
    ├── Workflows completing within SLA: 96%
    ├── Escalated workflows: 2
    └── avg time to escalation: 4.2h
```

### Failure Alerts

| Failure Type | Alert Channel | Severity | Action |
|-------------|---------------|----------|--------|
| Workflow execution error | Slack + Email | High | Notify workflow owner |
| Consecutive failures (3+) | SMS + Slack | Critical | Notify DevOps |
| SLA breach | Slack | Medium | Notify workflow owner |
| Trigger backlog (>100) | Dashboard | Warning | Scale consumer group |

---

## 7. Integration with Wave 2

### NBA → Workflow

```python
# When NBA recommendation is accepted, convert to workflow execution
class NBAWorkflowBridge:
    async def on_nba_accepted(self, event: DomainEvent):
        nba = event.data['nba']
        opportunity_id = event.data['opportunity_id']

        # Check if there's a workflow template for this NBA action
        template = await self.find_template_for_action(nba.action)
        if template:
            execution = await self.engine.execute(template, ExecutionContext(
                entity_type='opportunity',
                entity_id=opportunity_id,
                tenant_id=event.tenant_id,
            ))
            await self.event_bus.emit(Event(
                type="workflow.started_from_nba",
                data={"nba_id": nba.id, "execution_id": execution.id}
            ))
```

### Playbook → Workflow

```python
# Playbook steps become workflow templates
class PlaybookWorkflowConverter:
    def convert(self, playbook: Playbook) -> Workflow:
        steps = []
        for ps in playbook.stages:
            for action in ps.actions:
                steps.append(self._action_to_step(action))

        return Workflow(
            name=playbook.name,
            description=playbook.description,
            trigger=WorkflowTrigger(
                type='event',
                config=EventTriggerConfig(
                    event_type='opportunity.stage_changed',
                    filter=DomainFilter(field='stage', operator='==', value=ps.stage),
                )
            ),
            steps=steps,
        )
```

---

## 8. Performance & Scalability

| Metric | Budget | Scaling Strategy |
|--------|--------|-----------------|
| Workflow execution start | < 1s from trigger | Pre-warm action containers, connection pooling |
| Step execution (email) | < 2s | Async I/O, connection reuse |
| Step execution (webhook) | < 5s (configurable timeout) | Timeout + retry with backoff |
| Visual builder load | < 2s | Lazy-load actions, paginate templates |
| Execution trace query | < 500ms | Indexed by workflow_id + tenant_id, time-partitioned |
| Concurrent executions | 500+ per tenant | Horizontal scaling of engine workers |

---

*Workflow Automation Architecture complete. Ready for Sprint 12 implementation.*
