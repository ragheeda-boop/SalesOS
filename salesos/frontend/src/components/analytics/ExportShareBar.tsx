"use client";

import { useState } from "react";
import { cn } from "@salesos/ui";
import {
  Badge,
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
} from "@salesos/ui";
import {
  Share2,
  FileText,
  FileSpreadsheet,
  Calendar,
  Mail,
  X,
  Check,
  Clock,
} from "lucide-react";

interface ShareRecipient {
  email: string;
  permission: "view" | "edit" | "admin";
}

const CADENCE_OPTIONS = [
  { value: "daily" as const, label: "Daily" },
  { value: "weekly" as const, label: "Weekly" },
  { value: "monthly" as const, label: "Monthly" },
];

export function ExportShareBar({
  reportName: _reportName,
}: {
  reportName?: string;
}) {
  const [showShareModal, setShowShareModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [exporting, setExporting] = useState<"pdf" | "csv" | null>(null);
  const [exported, setExported] = useState<"pdf" | "csv" | null>(null);
  const [shareEmail, setShareEmail] = useState("");
  const [sharePermission, setSharePermission] = useState<
    "view" | "edit" | "admin"
  >("view");
  const [recipients, setRecipients] = useState<ShareRecipient[]>([]);
  const [scheduleCadence, setScheduleCadence] = useState<
    "daily" | "weekly" | "monthly"
  >("weekly");
  const [scheduleRecipients, setScheduleRecipients] = useState<string[]>([]);
  const [scheduleEmail, setScheduleEmail] = useState("");
  const [scheduled, setScheduled] = useState(false);
  const [shared, setShared] = useState(false);

  const handleExport = async (format: "pdf" | "csv") => {
    setExporting(format);
    await new Promise((r) => setTimeout(r, 1500));
    setExporting(null);
    setExported(format);
    setTimeout(() => setExported(null), 3000);
  };

  const handleAddRecipient = () => {
    if (shareEmail.trim() && !recipients.find((r) => r.email === shareEmail)) {
      setRecipients([
        ...recipients,
        { email: shareEmail.trim(), permission: sharePermission },
      ]);
      setShareEmail("");
    }
  };

  const handleRemoveRecipient = (email: string) => {
    setRecipients(recipients.filter((r) => r.email !== email));
  };

  const handleShare = () => {
    setShared(true);
    setShowShareModal(false);
    setTimeout(() => setShared(false), 3000);
  };

  const handleAddScheduleRecipient = () => {
    if (scheduleEmail.trim() && !scheduleRecipients.includes(scheduleEmail)) {
      setScheduleRecipients([...scheduleRecipients, scheduleEmail.trim()]);
      setScheduleEmail("");
    }
  };

  const handleSchedule = () => {
    setScheduled(true);
    setShowScheduleModal(false);
    setTimeout(() => setScheduled(false), 3000);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        {/* Export PDF */}
        <button
          onClick={() => handleExport("pdf")}
          disabled={exporting === "pdf"}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition",
            exported === "pdf"
              ? "border-green-500 bg-[var(--status-success-bg)] text-[var(--status-success-text)]"
              : "border-[var(--border-default)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]",
          )}
        >
          {exporting === "pdf" ? (
            <Clock className="h-3.5 w-3.5 animate-spin" />
          ) : exported === "pdf" ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <FileText className="h-3.5 w-3.5" />
          )}
          PDF
        </button>

        {/* Export CSV */}
        <button
          onClick={() => handleExport("csv")}
          disabled={exporting === "csv"}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition",
            exported === "csv"
              ? "border-green-500 bg-[var(--status-success-bg)] text-[var(--status-success-text)]"
              : "border-[var(--border-default)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]",
          )}
        >
          {exporting === "csv" ? (
            <Clock className="h-3.5 w-3.5 animate-spin" />
          ) : exported === "csv" ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <FileSpreadsheet className="h-3.5 w-3.5" />
          )}
          CSV
        </button>

        {/* Share */}
        <Modal open={showShareModal} onOpenChange={setShowShareModal}>
          <ModalTrigger asChild>
            <button className="flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition">
              <Share2 className="h-3.5 w-3.5" /> Share
            </button>
          </ModalTrigger>
          <ModalContent>
            <ModalHeader>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                Share Dashboard
              </h2>
            </ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-[var(--text-muted)]">
                    Add People
                  </label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      value={shareEmail}
                      onChange={(e) => setShareEmail(e.target.value)}
                      placeholder="email@company.com"
                      className="flex-1"
                      onKeyDown={(e) =>
                        e.key === "Enter" && handleAddRecipient()
                      }
                    />
                    <select
                      value={sharePermission}
                      onChange={(e) =>
                        setSharePermission(
                          e.target.value as "view" | "edit" | "admin",
                        )
                      }
                      className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-xs"
                    >
                      <option value="view">Can view</option>
                      <option value="edit">Can edit</option>
                      <option value="admin">Admin</option>
                    </select>
                    <button
                      onClick={handleAddRecipient}
                      className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1 text-xs text-white hover:opacity-90 transition"
                    >
                      Add
                    </button>
                  </div>
                </div>

                {recipients.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">
                      Recipients ({recipients.length})
                    </p>
                    {recipients.map((r) => (
                      <div
                        key={r.email}
                        className="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] px-3 py-2"
                      >
                        <div className="flex items-center gap-2">
                          <Mail className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                          <span className="text-xs text-[var(--text-primary)]">
                            {r.email}
                          </span>
                          <Badge
                            variant={
                              r.permission === "admin"
                                ? "danger"
                                : r.permission === "edit"
                                  ? "warning"
                                  : "outline"
                            }
                          >
                            {r.permission}
                          </Badge>
                        </div>
                        <button
                          onClick={() => handleRemoveRecipient(r.email)}
                          className="text-[var(--text-muted)] hover:text-[var(--status-danger-text)] transition"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ModalBody>
            <ModalFooter>
              <button
                onClick={() => setShowShareModal(false)}
                className="rounded-lg border border-[var(--border-default)] px-4 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
              >
                Cancel
              </button>
              <button
                onClick={handleShare}
                disabled={recipients.length === 0}
                className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition disabled:opacity-50"
              >
                Share with {recipients.length} people
              </button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Schedule */}
        <Modal open={showScheduleModal} onOpenChange={setShowScheduleModal}>
          <ModalTrigger asChild>
            <button className="flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition">
              <Calendar className="h-3.5 w-3.5" /> Schedule
            </button>
          </ModalTrigger>
          <ModalContent>
            <ModalHeader>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                Schedule Report
              </h2>
            </ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-[var(--text-muted)]">
                    Cadence
                  </label>
                  <div className="flex gap-2 mt-1">
                    {CADENCE_OPTIONS.map((c) => (
                      <button
                        key={c.value}
                        onClick={() => setScheduleCadence(c.value)}
                        className={cn(
                          "rounded-lg px-3 py-1.5 text-xs font-medium transition",
                          scheduleCadence === c.value
                            ? "bg-[var(--muhide-orange)] text-white"
                            : "border border-[var(--border-default)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]",
                        )}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-xs text-[var(--text-muted)]">
                    Recipients
                  </label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      value={scheduleEmail}
                      onChange={(e) => setScheduleEmail(e.target.value)}
                      placeholder="email@company.com"
                      className="flex-1"
                      onKeyDown={(e) =>
                        e.key === "Enter" && handleAddScheduleRecipient()
                      }
                    />
                    <button
                      onClick={handleAddScheduleRecipient}
                      className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1 text-xs text-white hover:opacity-90 transition"
                    >
                      Add
                    </button>
                  </div>
                </div>

                {scheduleRecipients.length > 0 && (
                  <div className="space-y-2">
                    {scheduleRecipients.map((email) => (
                      <div
                        key={email}
                        className="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] px-3 py-2"
                      >
                        <span className="text-xs text-[var(--text-primary)]">
                          {email}
                        </span>
                        <button
                          onClick={() =>
                            setScheduleRecipients(
                              scheduleRecipients.filter((e) => e !== email),
                            )
                          }
                          className="text-[var(--text-muted)] hover:text-[var(--status-danger-text)] transition"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ModalBody>
            <ModalFooter>
              <button
                onClick={() => setShowScheduleModal(false)}
                className="rounded-lg border border-[var(--border-default)] px-4 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSchedule}
                disabled={scheduleRecipients.length === 0}
                className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition disabled:opacity-50"
              >
                Schedule {scheduleCadence} report
              </button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Status badges */}
        {shared && <Badge variant="success">Shared!</Badge>}
        {scheduled && <Badge variant="success">Scheduled!</Badge>}
      </div>
    </>
  );
}
