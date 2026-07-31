"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "@/lib/i18n";
import {
  DataTable,
  Badge,
  Button,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  EmptyState,
  Input,
  Textarea,
  Select,
  useToast,
} from "@salesos/ui";
import {
  ArrowLeft,
  Plus,
  Settings,
  Trash2,
  Edit3,
  AlertTriangle,
  RefreshCw,
  FileText,
} from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import api from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { decisionKeys } from "@/lib/queryKeys";

const DOMAIN_OPTIONS = [
  { label: "Company", value: "company" },
  { label: "Opportunity", value: "opportunity" },
  { label: "Scoring", value: "scoring" },
  { label: "Workflow", value: "workflow" },
  { label: "AI", value: "ai" },
  { label: "Timeline", value: "timeline" },
  { label: "CRM", value: "crm" },
];

const DOMAIN_VARIANT: Record<
  string,
  "success" | "warning" | "danger" | "default" | "primary"
> = {
  company: "primary",
  opportunity: "success",
  scoring: "warning",
  workflow: "default",
  ai: "danger",
  timeline: "primary",
  crm: "success",
};

interface DecisionTemplate {
  id: string;
  name: string;
  description: string;
  domain: string;
  type: string;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  usage_count?: number;
}

interface TemplateListResponse {
  items: DecisionTemplate[];
  total: number;
}

function formatDate(dateStr: string): string {
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

export default function DecisionTemplatesPage() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [modalOpen, setModalOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<DecisionTemplate | null>(
    null,
  );
  const [deleteConfirm, setDeleteConfirm] = useState<DecisionTemplate | null>(
    null,
  );
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    domain: "company",
    type: "nba",
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [...decisionKeys.all, "templates"],
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/templates", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data as TemplateListResponse;
    },
    staleTime: 30_000,
  });

  const createTemplate = useMutation({
    mutationFn: async (values: typeof formData) => {
      const response = await api.post("/api/v1/decision/templates", values, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...decisionKeys.all, "templates"],
      });
      toast({ variant: "success", title: t("decisions.template_created") });
      setModalOpen(false);
      resetForm();
    },
    onError: () => {
      toast({ variant: "error", title: t("decisions.template_create_failed") });
    },
  });

  const updateTemplate = useMutation({
    mutationFn: async ({ id, ...values }: { id: string } & typeof formData) => {
      const response = await api.put(
        `/api/v1/decision/templates/${id}`,
        values,
        {
          headers: { "X-Tenant-Id": getTenantId() },
        },
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...decisionKeys.all, "templates"],
      });
      toast({ variant: "success", title: t("decisions.template_updated") });
      setModalOpen(false);
      setEditTemplate(null);
      resetForm();
    },
    onError: () => {
      toast({ variant: "error", title: t("decisions.template_update_failed") });
    },
  });

  const deleteTemplate = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/decision/templates/${id}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...decisionKeys.all, "templates"],
      });
      toast({ variant: "success", title: t("decisions.template_deleted") });
      setDeleteConfirm(null);
    },
    onError: () => {
      toast({ variant: "error", title: t("decisions.template_delete_failed") });
    },
  });

  const resetForm = useCallback(() => {
    setFormData({ name: "", description: "", domain: "company", type: "nba" });
  }, []);

  const openCreate = useCallback(() => {
    setEditTemplate(null);
    resetForm();
    setModalOpen(true);
  }, [resetForm]);

  const openEdit = useCallback((template: DecisionTemplate) => {
    setEditTemplate(template);
    setFormData({
      name: template.name,
      description: template.description,
      domain: template.domain,
      type: template.type,
    });
    setModalOpen(true);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!formData.name.trim()) return;
    if (editTemplate) {
      await updateTemplate.mutateAsync({ id: editTemplate.id, ...formData });
    } else {
      await createTemplate.mutateAsync(formData);
    }
  }, [formData, editTemplate, createTemplate, updateTemplate]);

  const templates = data?.items || [];

  const columns: ColumnDef<DecisionTemplate>[] = useMemo(
    () => [
      {
        accessorKey: "name",
        header: t("decisions.template_name"),
        cell: ({ row }) => (
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
              <FileText className="h-4 w-4 text-[var(--text-secondary)]" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {row.original.name}
              </p>
              {row.original.description && (
                <p className="text-xs text-[var(--text-muted)] truncate max-w-[300px]">
                  {row.original.description}
                </p>
              )}
            </div>
          </div>
        ),
      },
      {
        accessorKey: "domain",
        header: t("decisions.domain"),
        cell: ({ row }) => (
          <Badge variant={DOMAIN_VARIANT[row.original.domain] || "default"}>
            {row.original.domain}
          </Badge>
        ),
        size: 110,
      },
      {
        accessorKey: "type",
        header: t("decisions.type"),
        cell: ({ row }) => (
          <span className="text-sm text-[var(--text-secondary)]">
            {row.original.type}
          </span>
        ),
        size: 100,
      },
      {
        accessorKey: "is_active",
        header: t("labels.status"),
        cell: ({ row }) => (
          <Badge variant={row.original.is_active ? "success" : "default"}>
            {row.original.is_active ? t("status.active") : t("status.inactive")}
          </Badge>
        ),
        size: 90,
      },
      {
        accessorKey: "usage_count",
        header: t("decisions.usage"),
        cell: ({ row }) => (
          <span className="text-sm text-[var(--text-secondary)]">
            {row.original.usage_count ?? 0}
          </span>
        ),
        size: 80,
      },
      {
        accessorKey: "updated_at",
        header: t("labels.updated"),
        cell: ({ row }) => (
          <span className="text-xs text-[var(--text-muted)] whitespace-nowrap">
            {formatDate(row.original.updated_at)}
          </span>
        ),
        size: 120,
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => openEdit(row.original)}
              leftIcon={<Edit3 className="h-3.5 w-3.5" />}
            >
              {t("common.edit")}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDeleteConfirm(row.original)}
              className="text-[var(--status-danger-text)] hover:bg-[var(--status-danger-bg)]"
              leftIcon={<Trash2 className="h-3.5 w-3.5" />}
            >
              {t("common.delete")}
            </Button>
          </div>
        ),
        size: 160,
      },
    ],
    [t, openEdit],
  );

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState
          icon={
            <AlertTriangle className="h-10 w-10 text-[var(--status-danger-text)]" />
          }
          title={t("decisions.load_error")}
          description={(error as Error)?.message || t("decisions.check_server")}
          action={{ label: t("common.retry"), onClick: () => refetch() }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/decisions"
            className="inline-flex items-center gap-1 text-sm text-[var(--text-muted)] hover:text-[var(--muhide-orange)]"
          >
            <ArrowLeft className="h-4 w-4" />
            {t("decisions.back_to_center")}
          </Link>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
          {t("decisions.new_template")}
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          {t("decisions.templates_title")}
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          {t("decisions.templates_subtitle")}
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <DataTable<DecisionTemplate>
          columns={columns}
          data={templates}
          loading={isLoading}
          emptyState={{
            icon: <Settings className="h-10 w-10" />,
            title: t("decisions.no_templates"),
            description: t("decisions.no_templates_hint"),
            action: { label: t("decisions.new_template"), onClick: openCreate },
          }}
        />
      </div>

      <Modal open={modalOpen} onOpenChange={setModalOpen}>
        <ModalContent>
          <ModalHeader>
            {editTemplate
              ? t("decisions.edit_template")
              : t("decisions.new_template")}
          </ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  {t("decisions.template_name")} *
                </label>
                <Input
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder={t("decisions.template_name_placeholder")}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                  {t("decisions.description")}
                </label>
                <Textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder={t("decisions.template_description_placeholder")}
                  rows={3}
                  resize="vertical"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                    {t("decisions.domain")}
                  </label>
                  <Select
                    options={DOMAIN_OPTIONS}
                    value={formData.domain}
                    onChange={(v) => setFormData({ ...formData, domain: v })}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                    {t("decisions.type")}
                  </label>
                  <Input
                    value={formData.type}
                    onChange={(e) =>
                      setFormData({ ...formData, type: e.target.value })
                    }
                    placeholder="e.g. nba, risk_alert"
                  />
                </div>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => {
                setModalOpen(false);
                setEditTemplate(null);
                resetForm();
              }}
            >
              {t("common.cancel")}
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={
                !formData.name.trim() ||
                createTemplate.isPending ||
                updateTemplate.isPending
              }
              leftIcon={
                createTemplate.isPending || updateTemplate.isPending ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : undefined
              }
            >
              {createTemplate.isPending || updateTemplate.isPending
                ? t("common.saving")
                : editTemplate
                  ? t("common.save")
                  : t("common.create")}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <ModalContent>
          <ModalHeader>{t("decisions.confirm_delete_template")}</ModalHeader>
          <ModalBody>
            <div className="space-y-3">
              <p className="text-[var(--text-secondary)]">
                {t("decisions.delete_template_message", {
                  name: deleteConfirm?.name || "",
                })}
              </p>
              <p className="text-sm text-danger-600">
                {t("decisions.delete_irreversible")}
              </p>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={() =>
                deleteConfirm && deleteTemplate.mutateAsync(deleteConfirm.id)
              }
              disabled={deleteTemplate.isPending}
              className="bg-danger-600 text-white hover:bg-danger-700 focus:ring-danger-500"
              leftIcon={
                deleteTemplate.isPending ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )
              }
            >
              {deleteTemplate.isPending
                ? t("common.deleting")
                : t("common.delete")}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
