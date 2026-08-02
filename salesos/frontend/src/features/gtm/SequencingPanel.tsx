"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useAdvanceEnrollment,
  useCancelEnrollment,
  useCreateSequence,
  useEnrollContact,
  useEnrollmentDetail,
  useEnrollmentList,
  usePauseEnrollment,
  useResumeEnrollment,
  useSequenceDetail,
  useSequenceList,
  useSequencingMeta,
} from "@/lib/hooks/sequencingQueries";
import type { SequenceDefinition, SequenceEnrollment } from "@/lib/api";
import {
  SEQUENCING_HONESTY,
  SEQUENCING_NON_GOALS,
} from "@/features/gtm/sequencingHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/** FE-S11-09 — tip email sequencing. Not Production GO / RAG GO. */
export function SequencingPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useSequencingMeta();
  const listQuery = useSequenceList();
  const enrollmentsQuery = useEnrollmentList();
  const createMutation = useCreateSequence();
  const enrollMutation = useEnrollContact();
  const advanceMutation = useAdvanceEnrollment();
  const pauseMutation = usePauseEnrollment();
  const resumeMutation = useResumeEnrollment();
  const cancelMutation = useCancelEnrollment();

  const [selectedSeqId, setSelectedSeqId] = useState<string | null>(null);
  const [selectedEnrollId, setSelectedEnrollId] = useState<string | null>(null);
  const seqDetail = useSequenceDetail(selectedSeqId);
  const enrollDetail = useEnrollmentDetail(selectedEnrollId);

  const [name, setName] = useState("Pilot email sequence");
  const [step1Subject, setStep1Subject] = useState("Intro");
  const [step1Body, setStep1Body] = useState("Hello — tip step 1.");
  const [step1Day, setStep1Day] = useState("0");
  const [step2Subject, setStep2Subject] = useState("Follow-up");
  const [step2Body, setStep2Body] = useState("Checking in — tip step 2.");
  const [step2Day, setStep2Day] = useState("3");
  const [contactEmail, setContactEmail] = useState("pilot@example.com");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (hydrated) return;
    const seq = searchParams.get("sequence");
    if (seq) setSelectedSeqId(seq);
    const enr = searchParams.get("enrollment");
    if (enr) setSelectedEnrollId(enr);
    const email = searchParams.get("email");
    if (email?.trim()) setContactEmail(email.trim());
    setHydrated(true);
  }, [searchParams, hydrated]);

  function loadSequence(row: SequenceDefinition) {
    setSelectedSeqId(row.id);
    setName(row.name);
    const s0 = row.steps[0];
    const s1 = row.steps[1];
    if (s0) {
      setStep1Subject(s0.subject);
      setStep1Body(s0.body);
      setStep1Day(String(s0.day_offset));
    }
    if (s1) {
      setStep2Subject(s1.subject);
      setStep2Body(s1.body);
      setStep2Day(String(s1.day_offset));
    }
  }

  function loadEnrollment(row: SequenceEnrollment) {
    setSelectedEnrollId(row.id);
    setSelectedSeqId(row.sequence_id);
    setContactEmail(row.contact_email);
  }

  function onEnrollAction(
    label: string,
    mut: {
      mutate: (
        id: string,
        opts: {
          onSuccess: (row: SequenceEnrollment) => void;
          onError: (err: unknown) => void;
        },
      ) => void;
    },
    id: string,
  ) {
    mut.mutate(id, {
      onSuccess: (row) => {
        setSelectedEnrollId(row.id);
        toast({
          title: label,
          description: `status=${row.status} · step ${row.current_step_index}`,
          variant: "success",
        });
      },
      onError: (err) => {
        toast({
          title: `${label} failed`,
          description: getApiError(err),
          variant: "error",
        });
      },
    });
  }

  const activeEnroll = enrollDetail.data;

  return (
    <div className="space-y-4" data-testid="sequencing-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="sequencing-honesty"
      >
        {SEQUENCING_HONESTY} Non-goals: {SEQUENCING_NON_GOALS.join("; ")}. Not
        Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="sequencing-meta"
        >
          <p>
            {metaQuery.data.object} · channels{" "}
            {(
              metaQuery.data.channels ??
              (metaQuery.data.channel ? [metaQuery.data.channel] : [])
            ).join(", ") || "email"}
            {metaQuery.data.linkedin_policy
              ? ` · LI policy: ${metaQuery.data.linkedin_policy}`
              : ""}
          </p>
          <p data-testid="sequencing-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
        </div>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">
          {getApiError(metaQuery.error)}
        </p>
      ) : (
        <Spinner />
      )}

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          data-testid="sequencing-refresh"
          onClick={() => {
            void listQuery.refetch();
            void enrollmentsQuery.refetch();
            void metaQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <span
          className="text-xs text-[var(--text-muted)]"
          data-testid="sequencing-counts"
        >
          {listQuery.data?.length ?? 0} sequence(s) ·{" "}
          {enrollmentsQuery.data?.length ?? 0} enrollment(s)
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <ul
          className="max-h-40 space-y-1 overflow-y-auto rounded border border-[var(--border-default)] p-2"
          data-testid="sequencing-list"
        >
          {(listQuery.data ?? []).length === 0 ? (
            <li className="text-xs text-[var(--text-muted)]">No sequences.</li>
          ) : (
            (listQuery.data ?? []).map((row) => (
              <li key={row.id}>
                <button
                  type="button"
                  className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-[var(--bg-muted)] ${
                    selectedSeqId === row.id
                      ? "bg-[var(--bg-muted)] font-medium"
                      : ""
                  }`}
                  data-testid="sequencing-row"
                  onClick={() => loadSequence(row)}
                >
                  {row.name} · {row.step_count} step(s)
                </button>
              </li>
            ))
          )}
        </ul>
        <ul
          className="max-h-40 space-y-1 overflow-y-auto rounded border border-[var(--border-default)] p-2"
          data-testid="sequencing-enrollment-list"
        >
          {(enrollmentsQuery.data ?? []).length === 0 ? (
            <li className="text-xs text-[var(--text-muted)]">
              No enrollments.
            </li>
          ) : (
            (enrollmentsQuery.data ?? []).map((row) => (
              <li key={row.id}>
                <button
                  type="button"
                  className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-[var(--bg-muted)] ${
                    selectedEnrollId === row.id
                      ? "bg-[var(--bg-muted)] font-medium"
                      : ""
                  }`}
                  data-testid="sequencing-enrollment-row"
                  onClick={() => loadEnrollment(row)}
                >
                  {row.contact_email} · {row.status}
                </button>
              </li>
            ))
          )}
        </ul>
      </div>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="sequencing-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim() || !step1Subject.trim()) {
            toast({
              title: "Sequence required",
              description: "Name + step 1 subject required.",
              variant: "error",
            });
            return;
          }
          const steps = [
            {
              day_offset: Number(step1Day) || 0,
              channel: "email",
              subject: step1Subject.trim(),
              body: step1Body,
            },
          ];
          if (step2Subject.trim()) {
            steps.push({
              day_offset: Number(step2Day) || 0,
              channel: "email",
              subject: step2Subject.trim(),
              body: step2Body,
            });
          }
          createMutation.mutate(
            { name: name.trim(), steps },
            {
              onSuccess: (row) => {
                setSelectedSeqId(row.id);
                toast({
                  title: "Sequence created",
                  description: `${row.step_count} email step(s)`,
                  variant: "success",
                });
              },
              onError: (err) => {
                toast({
                  title: "Create failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold">Create sequence (email only)</h2>
        <Input
          label="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          data-testid="sequencing-name"
        />
        <Input
          label="step1 subject"
          value={step1Subject}
          onChange={(e) => setStep1Subject(e.target.value)}
          data-testid="sequencing-step1-subject"
        />
        <Input
          label="step1 body"
          value={step1Body}
          onChange={(e) => setStep1Body(e.target.value)}
          data-testid="sequencing-step1-body"
        />
        <Input
          label="step1 day_offset"
          value={step1Day}
          onChange={(e) => setStep1Day(e.target.value)}
          className="max-w-[8rem]"
          data-testid="sequencing-step1-day"
        />
        <Input
          label="step2 subject (optional)"
          value={step2Subject}
          onChange={(e) => setStep2Subject(e.target.value)}
          data-testid="sequencing-step2-subject"
        />
        <Input
          label="step2 body"
          value={step2Body}
          onChange={(e) => setStep2Body(e.target.value)}
          data-testid="sequencing-step2-body"
        />
        <Input
          label="step2 day_offset"
          value={step2Day}
          onChange={(e) => setStep2Day(e.target.value)}
          className="max-w-[8rem]"
          data-testid="sequencing-step2-day"
        />
        <Button
          type="submit"
          disabled={createMutation.isPending}
          data-testid="sequencing-create"
        >
          {createMutation.isPending ? "Creating…" : "Create sequence"}
        </Button>
      </form>

      {selectedSeqId ? (
        <form
          className="space-y-3 rounded border border-[var(--border-default)] p-4"
          data-testid="sequencing-enroll-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (!contactEmail.trim()) {
              toast({
                title: "Email required",
                description: "Provide contact_email.",
                variant: "error",
              });
              return;
            }
            enrollMutation.mutate(
              {
                sequenceId: selectedSeqId,
                body: { contact_email: contactEmail.trim() },
              },
              {
                onSuccess: (row) => {
                  setSelectedEnrollId(row.id);
                  toast({
                    title: "Enrolled",
                    description: `${row.contact_email} · ${row.status}`,
                    variant: "success",
                  });
                },
                onError: (err) => {
                  toast({
                    title: "Enroll failed",
                    description: getApiError(err),
                    variant: "error",
                  });
                },
              },
            );
          }}
        >
          <h2 className="text-sm font-semibold">Enroll contact</h2>
          {seqDetail.data ? (
            <p className="font-mono text-xs text-[var(--text-muted)]">
              sequence {seqDetail.data.id} · {seqDetail.data.step_count} step(s)
            </p>
          ) : null}
          <Input
            label="contact_email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            data-testid="sequencing-email"
          />
          <Button
            type="submit"
            disabled={enrollMutation.isPending}
            data-testid="sequencing-enroll"
          >
            {enrollMutation.isPending ? "Enrolling…" : "Enroll"}
          </Button>
        </form>
      ) : null}

      {selectedEnrollId ? (
        <div
          className="space-y-3 rounded border border-[var(--border-default)] p-4"
          data-testid="sequencing-enrollment-detail"
        >
          {enrollDetail.isLoading ? (
            <Spinner />
          ) : enrollDetail.isError ? (
            <p className="text-sm text-[var(--text-danger)]">
              {getApiError(enrollDetail.error)}
            </p>
          ) : activeEnroll ? (
            <>
              <p
                className="font-mono text-xs text-[var(--text-muted)]"
                data-testid="sequencing-enrollment-status"
              >
                {activeEnroll.id} · {activeEnroll.status} · step{" "}
                {activeEnroll.current_step_index} · bound=
                {String(activeEnroll.bound_to_task_activity)}
              </p>
              <ul
                className="space-y-1 text-xs"
                data-testid="sequencing-step-states"
              >
                {activeEnroll.step_states.map((s) => (
                  <li key={s.step_id}>
                    {s.step_id}: {s.status} (day {s.day_offset})
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  data-testid="sequencing-advance"
                  disabled={advanceMutation.isPending}
                  onClick={() =>
                    onEnrollAction("Advanced", advanceMutation, activeEnroll.id)
                  }
                >
                  Advance
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="sequencing-pause"
                  disabled={pauseMutation.isPending}
                  onClick={() =>
                    onEnrollAction("Paused", pauseMutation, activeEnroll.id)
                  }
                >
                  Pause
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="sequencing-resume"
                  disabled={resumeMutation.isPending}
                  onClick={() =>
                    onEnrollAction("Resumed", resumeMutation, activeEnroll.id)
                  }
                >
                  Resume
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="sequencing-cancel"
                  disabled={cancelMutation.isPending}
                  onClick={() =>
                    onEnrollAction("Cancelled", cancelMutation, activeEnroll.id)
                  }
                >
                  Cancel
                </Button>
              </div>
              {activeEnroll.task_bindings.length > 0 ? (
                <ul
                  className="space-y-1 text-xs"
                  data-testid="sequencing-task-bindings"
                >
                  {activeEnroll.task_bindings.map((t) => (
                    <li key={t.task_id}>
                      task {t.task_id}: {t.title}
                    </li>
                  ))}
                </ul>
              ) : null}
              {activeEnroll.activity_bindings.length > 0 ? (
                <ul
                  className="space-y-1 text-xs"
                  data-testid="sequencing-activity-bindings"
                >
                  {activeEnroll.activity_bindings.map((a) => (
                    <li key={a.activity_id}>
                      activity {a.activity_id}: {a.summary}
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}

      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/gtm/verification" className="underline">
          /gtm/verification
        </Link>
        {" · "}
        <Link href="/gtm" className="underline">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
