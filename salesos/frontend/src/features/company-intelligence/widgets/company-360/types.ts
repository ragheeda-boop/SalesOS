import type { Company360Response } from "@/lib/api";

export interface Company360ViewProps {
  companyId: string;
  company360?: Company360Response | null;
  isLoading?: boolean;
}

export interface Company360WidgetProps {
  companyId: string;
}
