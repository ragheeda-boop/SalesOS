"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  advanceEnrollment,
  cancelEnrollment,
  createSequence,
  enrollContact,
  getEnrollment,
  getSequence,
  getSequencingMeta,
  listEnrollments,
  listSequences,
  pauseEnrollment,
  resumeEnrollment,
  type EnrollBody,
  type SequenceCreateBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useSequencingMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.sequencingMeta(tenantId),
    queryFn: () => getSequencingMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useSequenceList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.sequenceList(tenantId),
    queryFn: () => listSequences(tenantId),
    staleTime: 10_000,
  });
}

export function useSequenceDetail(sequenceId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.sequenceDetail(tenantId, sequenceId ?? ""),
    queryFn: () => getSequence(tenantId, sequenceId as string),
    enabled: Boolean(sequenceId),
    staleTime: 10_000,
  });
}

export function useEnrollmentList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.enrollmentList(tenantId),
    queryFn: () => listEnrollments(tenantId),
    staleTime: 10_000,
  });
}

export function useEnrollmentDetail(enrollmentId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.enrollmentDetail(tenantId, enrollmentId ?? ""),
    queryFn: () => getEnrollment(tenantId, enrollmentId as string),
    enabled: Boolean(enrollmentId),
    staleTime: 10_000,
  });
}

function invalidateEnrollments(qc: ReturnType<typeof useQueryClient>) {
  const tenantId = getTenantId();
  qc.invalidateQueries({ queryKey: gtmKeys.enrollmentList(tenantId) });
}

export function useCreateSequence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SequenceCreateBody) => createSequence(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.sequenceList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.sequenceDetail(getTenantId(), row.id), row);
    },
  });
}

export function useEnrollContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sequenceId, body }: { sequenceId: string; body: EnrollBody }) =>
      enrollContact(getTenantId(), sequenceId, body),
    onSuccess: (row) => {
      invalidateEnrollments(qc);
      qc.setQueryData(gtmKeys.enrollmentDetail(getTenantId(), row.id), row);
    },
  });
}

export function useAdvanceEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enrollmentId: string) => advanceEnrollment(getTenantId(), enrollmentId),
    onSuccess: (row) => {
      invalidateEnrollments(qc);
      qc.setQueryData(gtmKeys.enrollmentDetail(getTenantId(), row.id), row);
    },
  });
}

export function usePauseEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enrollmentId: string) => pauseEnrollment(getTenantId(), enrollmentId),
    onSuccess: (row) => {
      invalidateEnrollments(qc);
      qc.setQueryData(gtmKeys.enrollmentDetail(getTenantId(), row.id), row);
    },
  });
}

export function useResumeEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enrollmentId: string) => resumeEnrollment(getTenantId(), enrollmentId),
    onSuccess: (row) => {
      invalidateEnrollments(qc);
      qc.setQueryData(gtmKeys.enrollmentDetail(getTenantId(), row.id), row);
    },
  });
}

export function useCancelEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enrollmentId: string) => cancelEnrollment(getTenantId(), enrollmentId),
    onSuccess: (row) => {
      invalidateEnrollments(qc);
      qc.setQueryData(gtmKeys.enrollmentDetail(getTenantId(), row.id), row);
    },
  });
}
