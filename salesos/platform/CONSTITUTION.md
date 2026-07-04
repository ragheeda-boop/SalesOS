# Platform Constitution

> SalesOS Kernel — المبادئ التي لا تُناقش إلا عبر ADR.
> صادق عليها في Sprint 3 بعد إثباتها معماريًا.

---

### المادة 1 — Replaceability

كل Capability يجب أن تكون قابلة للاستبدال (Replaceable).
يعني أي Executor يمكن استبداله دون تغيير SearchQuery أو SearchResult أو SearchPlanner.
الدليل: PostgreSQL B-Tree → Trigram → pgvector بنفس الـ Interface.

### المادة 2 — SDK Sovereignty

لا يجوز لأي Module تجاوز الـ SDK.
الـ SDK هو الطريق الوحيد للتعامل مع: Permissions, Audit, Events, Telemetry, Metadata.
أي Module يخترق هذه القاعدة يُعاد هيكلته فورًا.

### المادة 3 — Domain Events

كل تغيير في Domain — وليس فقط في Database — يولد Domain Event.
الـ Event يُسجل بـ CloudEvents 1.0 عبر EventBus.
لا توجد State Mutation بدون Event.

### المادة 4 — Testability Without UI

كل Capability يجب أن تكون قابلة للاختبار دون UI.
يعني كل Service يمكّن اختباره عبر Repository Interface وInMemory Store.
الـ UI مجرد مستهلك، وليس شرطًا لوجود الـ Feature.

### المادة 5 — Measurement Before Optimization

Performance يُقاس قبل تحسينه.
لا يُضاف أي تقنية (Index, Cache, Vector Store, Full-Text Search) إلا بعد Benchmark يثبت الحاجة.
الدليل: Sprint 3 أثبت أن PostgreSQL + Trigram تكفي لـ 100K شركة وأن pgvector ليس حلًا لمشكلة Selectivity.

### المادة 6 — Evidence Over Trends

التقنيات تُثبت بالأرقام، لا بالاتجاهات.
لا يُضاف pgvector, NoSQL, Neo4j, Queue, Cache, AI Model إلا إذا أثبت Benchmark فائدتها.
KPI: Precision, Recall, p95, CPU, Memory, Index Size.

### المادة 7 — Frozen Interface Protection

لا يُكسر أي Frozen Interface إلا عبر ADR.
حاليًا: SearchQuery, SearchResult, SearchPlanner — Frozen.
مستقبلًا قد تُضاف واجهات أخرى إلى القائمة بعد إثبات استقرارها.

### المادة 8 — Business Over Technology

Business Capability أهم من Technology Choice.
إذا تعارضت تقنية مع مبدأ Business، يُعاد تقييم التقنية وليس الـ Capability.
الـ Stack يخدم الـ Domain، وليس العكس.

### المادة 9 — Microservice Isolation Readiness

كل Module يمكن فصله إلى Microservice دون إعادة كتابة.
يعني الـ Module لا يعتمد على State مباشر من Module آخر — فقط Events و Contracts.
هذا يضمن عدم وجود "Big Ball of Mud" عند الحاجة للتوسع.

### المادة 10 — Data Sovereignty (AI)

البيانات هي الأصل (System of Record)، والـ AI مستهلك لها وليس مالكًا لها.
لا يُسمح لأي AI Agent أو Embedding Model بأن يكون المصدر الوحيد لأي حقيقة.
AI يُضيف — لا يستبدل — السجلات الأساسية.

---

*Amendments require a new ADR with: (1) Rationale, (2) Impact on existing articles, (3) Benchmark if performance-related.*
