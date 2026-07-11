"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listTasks, completeTask as apiCompleteTask, type TaskResponse } from "@/lib/api";
import { taskKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useTasks(priority?: string) {
  return useQuery<TaskResponse[]>({
    queryKey: taskKeys.list(priority ? { priority } : undefined),
    queryFn: () => listTasks(getTenantId(), priority),
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
}

export function useCompleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ taskId }: { taskId: string }) => {
      return apiCompleteTask(taskId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}
