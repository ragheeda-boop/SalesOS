import { PageHeader } from "../_components/page-header";
import { GhostButtonLink } from "../_components/states";

export default function V3ShellSpecPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Workspace shell"
        description="Chrome contract for /v3 — L2 nav, topbar, CmdK, Ask AI popup."
        actions={<GhostButtonLink href="/v3">Back to home</GhostButtonLink>}
      />

      <ul className="space-y-2 text-sm text-[var(--text-secondary)]">
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          L2 domain nav (collapsible sidebar)
        </li>
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          Topbar: workspace label, search trigger, CmdK hint, Ask AI, theme
        </li>
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          Ask AI is a modal popup only — no permanent AI rail or page tabs
        </li>
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          Command palette: go-to routes, filter, Escape closes
        </li>
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          Skip link + landmarks; routes under{" "}
          <code className="font-mono text-[12px]">/v3/*</code> only
        </li>
        <li className="flex gap-2">
          <span className="text-[var(--text-muted)]">·</span>
          Spec:{" "}
          <code className="font-mono text-[12px]">
            docs/design/salesos-v3/screens/shell/workspace-shell.md
          </code>
        </li>
      </ul>
    </div>
  );
}
