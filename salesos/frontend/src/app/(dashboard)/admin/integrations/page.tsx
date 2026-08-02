"use client";

import Link from "next/link";
import { IntegrationsStudioShell } from "@/features/admin/IntegrationsStudioShell";

/**
 * FE-S08-00/01 + STORY-08-07 pointer — Integration Hub Owner inventory.
 * Live Studio is tenant `/integrations` against Hub HTTP. Not Production GO.
 */
const BE_LANDED = [
  {
    id: "STORY-08-01",
    title: "SourceConnector Protocol + FakeSourceConnector",
    status: "BE landed",
  },
  {
    id: "STORY-08-02",
    title: "ExternalSystemConnection + Fernet credentials",
    status: "BE landed",
  },
  {
    id: "STORY-08-03",
    title: "FieldMappingConfig + drift job",
    status: "BE landed",
  },
  {
    id: "STORY-08-04",
    title: "Anti-Corruption Layer (OdooTranslator)",
    status: "BE landed",
  },
  {
    id: "STORY-08-05",
    title: "SyncRun + CAP-028 scheduling",
    status: "BE landed",
  },
] as const;

const FE_GATED = [
  {
    id: "STORY-08-06",
    title: "ConflictResolutionPolicy + Hub HTTP",
    status: "BE landed",
  },
  {
    id: "STORY-08-07",
    title: "Integrations Studio UI",
    status: "FE landed — /integrations",
  },
  {
    id: "FE-S08-08",
    title: "Conflict-policy Studio + Odoo honesty",
    status: "FE landed — conflict step",
  },
  {
    id: "FE-S08-09",
    title: "Active mapping load + tenant Integrations nav",
    status: "FE landed — map GET + nav",
  },
  {
    id: "FE-S08-10",
    title: "Studio detail + baseline_fields polish",
    status: "FE landed — detail/baseline/cmd",
  },
  {
    id: "FE-S08-11",
    title: "Studio URL deep-link polish",
    status: "FE landed — ?step=&connection=",
  },
  {
    id: "FE-S08-12",
    title: "Monitor SyncRun model filter + tip fields",
    status: "FE landed — runModel + finished_at",
  },
  {
    id: "FE-S08-13",
    title: "Schedule job_type + conflict tip defaults",
    status: "FE landed — job_type + tip defaults",
  },
  {
    id: "FE-S08-14",
    title: "Mapping version + schedule name + connection GET",
    status: "FE landed — version/name/refresh/cmd",
  },
  {
    id: "FE-S09-01",
    title: "Partner model presets + cr_number join honesty",
    status: "FE landed — res.partner presets",
  },
  {
    id: "FE-S09-02",
    title: "Opportunity model presets + stage honesty",
    status: "FE landed — crm.lead presets",
  },
  {
    id: "FE-S09-03",
    title: "InteractionNote presets + PII scrub honesty",
    status: "FE landed — mail.message presets",
  },
  {
    id: "FE-S09-04",
    title: "SupportTicket presets + stage honesty",
    status: "FE landed — helpdesk.ticket presets",
  },
] as const;

export default function AdminIntegrationsInventoryPage() {
  return (
    <div className="space-y-6 p-6" data-testid="admin-integrations-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Integration Hub
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Owner Console inventory for EPIC-08. DOM-021 plan gate applies when
          HTTP surfaces land. No invented connector APIs.
        </p>
      </div>

      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="owner-ops-integrations-honesty"
      >
        FE inventory: BE 08-01..06 + STORY-09-01/09-02 OdooAdapter landed.
        Tenant Studio (through FE-S09-01..03 partner / opportunity /
        InteractionNote presets) is at `/integrations`. Unlinked badge list
        still BE-blocked. Owner mint remains DEC-093 follow-up. Not Production
        GO / RAG GO.
      </p>

      <IntegrationsStudioShell />

      <section data-testid="admin-integrations-be-landed">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Backend landed
        </h2>
        <ul className="mt-2 space-y-2">
          {BE_LANDED.map((item) => (
            <li
              key={item.id}
              className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
              data-testid={`admin-integrations-item-${item.id}`}
            >
              <span className="font-medium">{item.id}</span> — {item.title}
              <span className="ml-2 text-xs text-[var(--text-muted)]">
                ({item.status})
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section data-testid="admin-integrations-fe-gated">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Gated / next
        </h2>
        <ul className="mt-2 space-y-2">
          {FE_GATED.map((item) => (
            <li
              key={item.id}
              className="rounded border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-secondary)]"
              data-testid={`admin-integrations-item-${item.id}`}
            >
              <span className="font-medium">{item.id}</span> — {item.title}
              <span className="ml-2 text-xs text-[var(--text-muted)]">
                ({item.status})
              </span>
            </li>
          ))}
        </ul>
      </section>

      <p className="text-xs text-[var(--text-muted)]">
        Return to{" "}
        <Link
          href="/admin"
          data-testid="admin-integrations-overview-link"
          className="underline"
        >
          Owner Console overview
        </Link>
        .
      </p>
    </div>
  );
}
