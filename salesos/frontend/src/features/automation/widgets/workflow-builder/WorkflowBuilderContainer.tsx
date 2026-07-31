"use client";

import { useState, useCallback } from "react";
import {
  useWorkflows,
  useCreateWorkflow,
  useUpdateWorkflow,
  useDeleteWorkflow,
  useExecuteWorkflow,
  type Workflow,
  type WorkflowStep,
} from "@/lib/workflowQueries";
import { WorkflowBuilderView } from "./WorkflowBuilderView";
import type { WorkflowBuilderViewProps } from "./WorkflowBuilderView";

function emptyStep(order: number): WorkflowStep {
  return {
    id: crypto.randomUUID?.() || `${Date.now()}`,
    type: "send_email",
    config: {},
    order,
  };
}

export function WorkflowBuilderContainer() {
  const { data: workflows, isLoading, error } = useWorkflows();
  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  const [editing, setEditing] = useState<Partial<Workflow> | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [confirmExecute, setConfirmExecute] = useState<string | null>(null);

  const handleCreate = useCallback(() => {
    setEditing({
      name: "",
      description: "",
      trigger_type: "manual",
      trigger_config: {},
      steps: [emptyStep(0)],
      status: "draft",
    });
    setShowForm(true);
  }, []);

  const handleEdit = useCallback((w: Workflow) => {
    setEditing({ ...w });
    setShowForm(true);
  }, []);

  const handleSave = useCallback(async () => {
    if (!editing) return;
    if (editing.id) {
      await updateWorkflow.mutateAsync(editing as Workflow);
    } else {
      await createWorkflow.mutateAsync(editing);
    }
    setShowForm(false);
    setEditing(null);
  }, [editing, createWorkflow, updateWorkflow]);

  const handleDelete = useCallback(
    async (id: string) => {
      if (confirm("هل أنت متأكد من حذف سير العمل هذا؟")) {
        await deleteWorkflow.mutateAsync(id);
      }
    },
    [deleteWorkflow],
  );

  const handleExecute = useCallback(
    async (id: string) => {
      setExecutingId(id);
      try {
        await executeWorkflow.mutateAsync(id);
      } finally {
        setExecutingId(null);
        setConfirmExecute(null);
      }
    },
    [executeWorkflow],
  );

  const addStep = useCallback(() => {
    if (!editing) return;
    const steps = [...(editing.steps || [])];
    steps.push(emptyStep(steps.length));
    setEditing({ ...editing, steps });
  }, [editing]);

  const removeStep = useCallback(
    (index: number) => {
      if (!editing) return;
      const steps =
        editing.steps
          ?.filter((_, i) => i !== index)
          .map((s, i) => ({ ...s, order: i })) || [];
      setEditing({ ...editing, steps });
    },
    [editing],
  );

  const updateStep = useCallback(
    (index: number, step: Partial<WorkflowStep>) => {
      if (!editing?.steps) return;
      const steps = editing.steps.map((s, i) =>
        i === index ? { ...s, ...step } : s,
      );
      setEditing({ ...editing, steps });
    },
    [editing],
  );

  const viewProps: WorkflowBuilderViewProps = {
    workflows,
    isLoading,
    error: error as Error | null,
    onCreate: handleCreate,
    onEdit: handleEdit,
    onDelete: handleDelete,
    onExecute: handleExecute,
    editing,
    showForm,
    confirmExecute,
    executingId,
    isSaving: createWorkflow.isPending || updateWorkflow.isPending,
    onFormClose: useCallback(() => {
      setShowForm(false);
      setEditing(null);
    }, []),
    onEditingChange: useCallback((w: Partial<Workflow>) => setEditing(w), []),
    onSave: handleSave,
    onAddStep: addStep,
    onRemoveStep: removeStep,
    onUpdateStep: updateStep,
    onConfirmExecute: useCallback(
      (id: string | null) => setConfirmExecute(id),
      [],
    ),
  };

  return <WorkflowBuilderView {...viewProps} />;
}
