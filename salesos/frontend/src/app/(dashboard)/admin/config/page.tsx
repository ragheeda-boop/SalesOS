"use client";

import { useState, useCallback, useEffect } from "react";
import {
  Button,
  Badge,
  Card,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useToast,
} from "@salesos/ui";
import {
  Save,
  CheckCircle2,
  Clock,
  FileCode2,
  Loader2,
  ChevronDown,
  ChevronUp,
  RotateCcw,
} from "lucide-react";
import {
  useAdminConfig,
  useSaveAdminConfig,
  useValidateAdminConfig,
} from "@/lib/hooks/adminQueries";
import type { AdminConfigVersion } from "@/lib/api";

export default function AdminConfigPage() {
  const { toast } = useToast();
  const { data: config, isLoading } = useAdminConfig();
  const saveMutation = useSaveAdminConfig();
  const validateMutation = useValidateAdminConfig();

  const [content, setContent] = useState("");
  const [showVersions, setShowVersions] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [showDiscardConfirm, setShowDiscardConfirm] = useState(false);

  // Sync editor when config loads
  useEffect(() => {
    if (config) setContent(config.content);
  }, [config]);

  useEffect(() => {
    setHasChanges(config ? content !== config.content : false);
  }, [content, config]);

  const handleValidate = useCallback(() => {
    validateMutation.mutate(content, {
      onSuccess: (result) => {
        if (result.valid) {
          toast({
            variant: "success",
            title: "Validation passed",
            description: "No syntax or semantic errors found.",
          });
        } else {
          toast({
            variant: "error",
            title: "Validation failed",
            description: result.errors.join(";"),
          });
        }
      },
      onError: () =>
        toast({ variant: "error", title: "Validation request failed" }),
    });
  }, [content, validateMutation, toast]);

  const handleSave = useCallback(async () => {
    try {
      await saveMutation.mutateAsync(content);
      setHasChanges(false);
      toast({
        variant: "success",
        title: "Config saved",
        description: "New version created successfully.",
      });
    } catch {
      toast({ variant: "error", title: "Failed to save config" });
    }
  }, [content, saveMutation, toast]);

  const handleDiscard = useCallback(() => {
    if (config) setContent(config.content);
    setShowDiscardConfirm(false);
    setHasChanges(false);
  }, [config]);

  const formatDateTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            System Config
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Edit the YAML configuration. Changes are validated before saving.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <Badge variant="warning" className="mr-1">
              Unsaved changes
            </Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowVersions(!showVersions)}
            leftIcon={<Clock className="h-4 w-4" />}
          >
            History
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleValidate}
            disabled={validateMutation.isPending}
            leftIcon={
              validateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )
            }
          >
            Validate
          </Button>
          <Button
            size="sm"
            onClick={() => setShowDiscardConfirm(true)}
            disabled={!hasChanges}
            leftIcon={<RotateCcw className="h-4 w-4" />}
          >
            Discard
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!hasChanges || saveMutation.isPending}
            leftIcon={
              saveMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )
            }
          >
            {saveMutation.isPending ? "Saving..." : "Save Config"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Editor */}
        <div className="lg:col-span-3">
          {isLoading ? (
            <Card className="p-12 text-center">
              <Spinner className="mx-auto h-6 w-6" />
              <p className="mt-2 text-sm text-[var(--text-muted)]">
                Loading config...
              </p>
            </Card>
          ) : (
            <Card className="overflow-hidden">
              <div className="flex items-center gap-2 border-b border-[var(--border-default)] px-4 py-2 bg-[var(--bg-secondary)]/50">
                <FileCode2 className="h-4 w-4 text-[var(--text-muted)]" />
                <span className="text-sm font-medium text-[var(--text-secondary)]">
                  system_config.yaml
                </span>
                <Badge variant="default" className="ml-auto text-[10px]">
                  v{config?.version ?? "—"}
                </Badge>
              </div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                spellCheck={false}
                className="w-full min-h-[600px] resize-y border-0 bg-[var(--bg-primary)] p-4 font-mono text-sm leading-relaxed text-[var(--text-primary)] focus:outline-none focus:ring-0"
                placeholder="# System configuration YAML..."
              />
            </Card>
          )}
        </div>

        {/* Version History Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-[var(--text-primary)]">
                Version History
              </h3>
              <button
                onClick={() => setShowVersions(!showVersions)}
                className="text-[var(--text-muted)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
              >
                {showVersions ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
            </div>

            {config?.versions?.length ? (
              <div className="space-y-2">
                {(showVersions
                  ? config.versions
                  : config.versions.slice(0, 5)
                ).map((v: AdminConfigVersion) => (
                  <div
                    key={v.version}
                    className={`rounded-lg border p-3 transition ${
                      v.version === config.version
                        ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5"
                        : "border-[var(--border-default)]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        v{v.version}
                      </span>
                      {v.version === config.version && (
                        <Badge variant="success" className="text-[10px]">
                          Current
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">
                      {formatDateTime(v.created_at)}
                    </p>
                    <p className="text-xs text-[var(--text-disabled)]">
                      {v.created_by}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[var(--text-muted)]">
                No version history
              </p>
            )}
          </Card>
        </div>
      </div>

      {/* Discard Confirm Modal */}
      <Modal open={showDiscardConfirm} onOpenChange={setShowDiscardConfirm}>
        <ModalContent>
          <ModalHeader>Discard Changes?</ModalHeader>
          <ModalBody>
            <p className="text-sm text-[var(--text-secondary)]">
              You have unsaved changes. Discarding will revert to the last saved
              version.
            </p>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              onClick={() => setShowDiscardConfirm(false)}
            >
              Keep Editing
            </Button>
            <Button variant="danger" onClick={handleDiscard}>
              Discard
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
