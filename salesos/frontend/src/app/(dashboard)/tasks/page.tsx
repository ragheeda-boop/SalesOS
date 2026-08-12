"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { Skeleton, EmptyState, Badge, cn } from "@salesos/ui";
import { useTenant } from "@/lib/hooks/useTenant";
import {
  CheckCircle2, Plus, Filter, RefreshCw,
  Building2, Handshake, Calendar
} from "lucide-react";

interface Task {
  id: string;
  title: string;
  priority: string;
  source?: string;
  company_id?: string;
  opportunity_id?: string;
  due_date?: string;
  completed: boolean;
  created_at: string;
}

const PRIORITY_LABELS: Record<string, string> = {
  high: "عاجل", medium: "متوسط", low: "منخفض",
};
const PRIORITY_COLORS: Record<string, string> = {
  high: "text-danger-600 bg-danger-50 border-danger-200",
  medium: "text-warning-600 bg-warning-50 border-warning-200",
  low: "text-success-600 bg-success-50 border-success-200",
};

export default function TasksPage() {
  const { tenantId } = useTenant();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "completed">("pending");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchTasks = useCallback(async () => {
    try {
      setRefreshing(true);
      const params: Record<string, string> = {};
      if (priorityFilter) params.priority = priorityFilter;
      const { data } = await api.get("/api/v1/tasks", {
        params,
        headers: { "X-Tenant-Id": tenantId },
      });
      setTasks(Array.isArray(data) ? data : data?.items || data?.tasks || []);
    } catch {
      // handled by empty state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [tenantId, priorityFilter]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const handleComplete = async (taskId: string) => {
    try {
      await api.put(`/api/v1/tasks/${taskId}/complete`, {}, {
        headers: { "X-Tenant-Id": tenantId },
      });
      setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, completed: true } : t)));
    } catch { /* handle gracefully */ }
  };

  const filtered = tasks.filter((t) => {
    if (filter === "pending") return !t.completed;
    if (filter === "completed") return t.completed;
    return true;
  });

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-[var(--text-primary)]">المهام</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchTasks}
            disabled={refreshing}
            className="inline-flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-medium hover:bg-[var(--bg-secondary)] disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", refreshing && "animate-spin")} />
          </button>
          <Link
            href="/tasks/new"
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
          >
            <Plus className="h-3.5 w-3.5" /> مهمة جديدة
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2">
        <span className="text-xs font-medium text-[var(--text-muted)]"><Filter className="h-3 w-3 inline mr-1" />تصفية</span>
        <div className="flex gap-1">
          {(["pending", "completed", "all"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                filter === f ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]" : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
              )}
            >
              {f === "pending" ? "المعلقة" : f === "completed" ? "المكتملة" : "الكل"}
            </button>
          ))}
        </div>
        <div className="h-4 w-px bg-[var(--border-default)]" />
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-primary)]"
        >
          <option value="">كل الأولويات</option>
          <option value="high">عاجل</option>
          <option value="medium">متوسط</option>
          <option value="low">منخفض</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="h-12 w-12" />}
          title={filter === "completed" ? "لا توجد مهام مكتملة" : "لا توجد مهام"}
          description={filter === "completed" ? "لم تكتمل أي مهمة بعد" : "لم يتم إنشاء مهام بعد"}
          action={filter !== "completed" ? { label: "إنشاء مهمة", onClick: () => {} } : undefined}
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((task) => (
            <div
              key={task.id}
              className={cn(
                "rounded-xl border bg-[var(--bg-primary)] p-4 transition-colors",
                task.completed ? "border-[var(--border-default)] opacity-60" : "border-[var(--border-default)]"
              )}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => handleComplete(task.id)}
                  disabled={task.completed}
                  className={cn(
                    "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors",
                    task.completed
                      ? "border-success-500 bg-success-500 text-white"
                      : "border-[var(--border-strong)] hover:border-success-400"
                  )}
                >
                  {task.completed && <CheckCircle2 className="h-3.5 w-3.5" />}
                </button>
                <div className="min-w-0 flex-1">
                  <div className={cn("text-sm font-medium", task.completed && "line-through text-[var(--text-muted)]")}>
                    {task.title}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Badge variant="default" className={cn("text-[10px]", PRIORITY_COLORS[task.priority] || "bg-[var(--bg-tertiary)]")}>
                      {PRIORITY_LABELS[task.priority] || task.priority}
                    </Badge>
                    {task.source && <span className="text-[10px] text-[var(--text-muted)]">{task.source}</span>}
                    {task.due_date && (
                      <span className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                        <Calendar className="h-3 w-3" /> {new Date(task.due_date).toLocaleDateString("ar-SA")}
                      </span>
                    )}
                    {task.company_id && (
                      <Link href={`/companies/${task.company_id}`} className="flex items-center gap-1 text-[10px] text-[var(--muhide-orange)] hover:underline">
                        <Building2 className="h-3 w-3" />
                      </Link>
                    )}
                    {task.opportunity_id && (
                      <Link href={`/opportunities/${task.opportunity_id}`} className="flex items-center gap-1 text-[10px] text-[var(--muhide-orange)] hover:underline">
                        <Handshake className="h-3 w-3" />
                      </Link>
                    )}
                  </div>
                </div>
                <span className="shrink-0 text-[10px] text-[var(--text-muted)]">
                  {new Date(task.created_at).toLocaleDateString("ar-SA")}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
