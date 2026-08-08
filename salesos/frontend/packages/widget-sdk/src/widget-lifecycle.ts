import { useEffect, useRef } from "react";
import type { WidgetStatus, WidgetMetadata, WidgetLifecycle as LifecycleHooks } from "./types";

export function useWidgetLifecycle(
  id: string,
  metadata: WidgetMetadata,
  status: WidgetStatus,
  hooks?: LifecycleHooks
) {
  const prevStatus = useRef<WidgetStatus>(status);
  const hooksRef = useRef(hooks);
  const metadataRef = useRef(metadata);
  hooksRef.current = hooks;
  metadataRef.current = metadata;

  useEffect(() => {
    hooksRef.current?.onMount?.({ id, metadata: metadataRef.current });
    return () => hooksRef.current?.onUnmount?.({ id, metadata: metadataRef.current });
  }, [id]);

  useEffect(() => {
    if (prevStatus.current !== status) {
      hooksRef.current?.onStatusChange?.({
        id,
        metadata: metadataRef.current,
        status,
        previous: prevStatus.current,
      });
      prevStatus.current = status;
    }
  });

  return {
    notifyRefresh: () => hooksRef.current?.onRefresh?.({ id, metadata: metadataRef.current }),
    notifyError: (error: Error) =>
      hooksRef.current?.onError?.({ id, metadata: metadataRef.current, error }),
  };
}
