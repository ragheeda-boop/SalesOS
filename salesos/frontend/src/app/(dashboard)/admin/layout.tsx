"use client";

import type { ReactNode } from "react";
import { OwnerConsoleShell } from "@/features/admin/OwnerConsoleShell";

/**
 * STORY-07-03 — Owner Console shell wraps all /admin/* routes.
 * Audience-isolated from tenant app. Not Production GO.
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  return <OwnerConsoleShell>{children}</OwnerConsoleShell>;
}
