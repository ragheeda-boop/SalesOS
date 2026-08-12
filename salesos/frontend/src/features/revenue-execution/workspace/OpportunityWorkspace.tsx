"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import Link from "next/link";
import { cn, Card, CardContent, CardHeader, Skeleton, Badge } from "@salesos/ui";
import { NBAWidget } from "../widgets/nba-widget/NBAWidget";
import {
  Building2, Users, Target, CheckCircle, AlertTriangle,
  XCircle, Activity, ShieldCheck
} from "lucide-react";

interface Opportunity {
  id: string;
  companyId: string;
  name: string;
  stage: string;
  value: number;
  currency: string;
  probability: number;
  health: string;
  expectedCloseDate?: string;
  ownerId: string;
  status: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

interface CompanySnapshot {
  id: string;
  name_ar?: string;
  name_en?: string;
  cr_number?: string;
  city?: string;
  status?: string;
}

interface OpportunityContact {
  id: string;
  contact_id: string;
  opportunity_id: string;
  role?: string;
  is_primary?: boolean;
  contact_name?: string;
  contact_email?: string;
  contact_position?: string;
}

interface OpportunityWorkspaceProps {
  opportunityId: string;
}

export function OpportunityWorkspace({ opportunityId }: OpportunityWorkspaceProps) {
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [company, setCompany] = useState<CompanySnapshot | null>(null);
  const [contacts, setContacts] = useState<OpportunityContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [contactsLoaded, setContactsLoaded] = useState(false);
  const [attributions, setAttributions] = useState<Record<string, unknown>[]>([]);
  const [attributionsLoaded, setAttributionsLoaded] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/api/v1/opportunities/${opportunityId}`);
        setOpportunity(data);

        // Fetch company snapshot if companyId exists
        if (data.companyId) {
          try {
            const companyRes = await api.get(`/api/v1/companies/${data.companyId}`);
            setCompany(companyRes.data);
          } catch {
            // Company fetch is best-effort
          }
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [opportunityId]);

  // Load ADR-030 contacts
  useEffect(() => {
    const loadContacts = async () => {
      try {
        const { data } = await api.get(`/api/v1/opportunity-contacts`, {
          params: { opportunity_id: opportunityId }
        });
        const items = data.items || data || [];
        // Enrich with contact details
        const enriched: OpportunityContact[] = [];
        for (const oc of items) {
          let contactDetail: Record<string, unknown> = {};
          try {
            const cr = await api.get(`/api/v1/contacts/${oc.contact_id}`);
            contactDetail = cr.data || {};
          } catch { /* best-effort */ }
          enriched.push({
            ...oc,
            contact_name: (contactDetail.name || oc.contact_name) as string,
            contact_email: (contactDetail.email || oc.contact_email) as string,
            contact_position: (contactDetail.position || oc.contact_position) as string,
          });
        }
        setContacts(enriched);
      } catch { /* contacts are optional */ }
      finally { setContactsLoaded(true); }
    };
    if (opportunity) loadContacts();
  }, [opportunityId, opportunity]);

  // Load ADR-031 attributions for this opportunity
  useEffect(() => {
    const loadAttr = async () => {
      try {
        const { data } = await api.get("/api/v1/attributions", {
          params: { opportunity_id: opportunityId, limit: 10 }
        });
        setAttributions(data.items || data || []);
      } catch { /* optional */ }
      finally { setAttributionsLoaded(true); }
    };
    if (opportunity) loadAttr();
  }, [opportunityId, opportunity]);

  if (loading) return <div className="animate-pulse h-96 bg-[var(--bg-tertiary)] rounded-xl" />;

  if (!opportunity)
    return (
      <div className="flex items-center justify-center h-96 text-[var(--text-muted)]">
        لم يتم العثور على الفرصة
      </div>
    );

  const stageLabels: Record<string, string> = {
    prospecting: "استكشاف", qualification: "تأهيل",
    proposal: "عرض", negotiation: "تفاوض",
    closed_won: "فوز", closed_lost: "خسارة",
  };

  const healthLabel: Record<string, string> = {
    healthy: "سليم", at_risk: "في خطر", critical: "حرج",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">{opportunity.name}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
              {stageLabels[opportunity.stage] || opportunity.stage}
            </span>
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {opportunity.value.toLocaleString()} {opportunity.currency}
            </span>
            <span
              className={cn(
                "text-xs px-2 py-0.5 rounded-full",
                opportunity.health === "healthy" && "bg-success-100 text-success-700",
                opportunity.health === "at_risk" && "bg-warning-100 text-warning-700",
                opportunity.health === "critical" && "bg-danger-100 text-danger-700"
              )}
            >
              {healthLabel[opportunity.health] || opportunity.health}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: NBA + Contacts + Activities */}
        <div className="lg:col-span-2 space-y-6">
          <section aria-label="Next Best Action">
            <NBAWidget opportunityId={opportunityId} />
          </section>

          {/* Contacts from ADR-030 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-[var(--text-muted)]" />
                <span className="text-sm font-semibold text-[var(--text-primary)]">جهات الاتصال</span>
                {contacts.length > 0 && (
                  <span className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">{contacts.length}</span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {contacts.length > 0 ? (
                <div className="space-y-2">
                  {contacts.map((c) => (
                    <Link
                      key={c.id}
                      href={`/contacts/${c.contact_id}`}
                      className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)] hover:bg-[var(--bg-secondary)] transition-colors"
                    >
                      <div className="w-10 h-10 rounded-full bg-[var(--muhide-orange)]/20 flex items-center justify-center text-[var(--muhide-orange)] font-semibold shrink-0">
                        {(c.contact_name || "?")[0]}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-[var(--text-primary)]">{c.contact_name || c.contact_id}</div>
                        {c.contact_position && <div className="text-sm text-[var(--text-secondary)]">{c.contact_position}</div>}
                        {c.contact_email && <div className="text-xs text-[var(--text-muted)] truncate">{c.contact_email}</div>}
                      </div>
                      <div className="shrink-0 flex flex-col items-end gap-1">
                        {c.is_primary && <Badge variant="default">أساسي</Badge>}
                        {c.role && <span className="text-[10px] text-[var(--text-muted)]">{c.role}</span>}
                      </div>
                    </Link>
                  ))}
                </div>
              ) : contactsLoaded ? (
                <p className="text-sm text-[var(--text-muted)] py-4 text-center">لا توجد جهات اتصال مرتبطة بهذه الفرصة</p>
              ) : (
                <div className="space-y-2">{Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
              )}
            </CardContent>
          </Card>

          {/* ADR-031 Attribution Activity */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-[var(--text-muted)]" />
                <span className="text-sm font-semibold text-[var(--text-primary)]">النشاطات المنسوبة</span>
                {attributions.length > 0 && (
                  <span className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">{attributions.length}</span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {attributions.length > 0 ? (
                <div className="space-y-2">
                  {attributions.map((a: Record<string, unknown>, i: number) => {
                    const methodLabels: Record<string, string> = {
                      explicit_reference: "مرجع مباشر", contact_match: "تطابق جهة اتصال",
                      company_match: "تطابق شركة", domain_match: "تطابق نطاق",
                    };
                    const stateColors: Record<string, string> = {
                      confirmed: "text-success-600 bg-success-50",
                      candidate: "text-warning-600 bg-warning-50",
                      ambiguous: "text-warning-600 bg-warning-50",
                      unresolved: "text-[var(--text-muted)] bg-[var(--bg-tertiary)]",
                    };
                    return (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border-default)]">
                        <ShieldCheck className="h-4 w-4 mt-0.5 text-[var(--muhide-orange)]/70 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-medium text-[var(--text-primary)]">
                            {String(a.activity_type || "").replace("_", " ")}
                            <span className="text-[var(--text-muted)] mx-1">·</span>
                            {methodLabels[String(a.resolution_method)] || String(a.resolution_method)}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-2">
                            <span className={cn("text-[10px] px-1.5 py-0.5 rounded", stateColors[String(a.resolution_state)] || "bg-[var(--bg-tertiary)]")}>
                              {String(a.resolution_state)}
                            </span>
                            {a.confidence != null && (
                              <span className="text-[10px] text-[var(--text-muted)]">
                                {(Number(a.confidence) * 100).toFixed(0)}%
                              </span>
                            )}
                            {Boolean(a.algorithm_version) && (
                              <span className="text-[10px] text-[var(--text-muted)]">{String(a.algorithm_version)}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : attributionsLoaded ? (
                <p className="text-sm text-[var(--text-muted)] py-4 text-center">لا توجد نشاطات منسوبة لهذه الفرصة</p>
              ) : (
                <div className="space-y-2">{Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Company Snapshot + Deal Health */}
        <div className="space-y-6">
          {/* Company Snapshot */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-[var(--text-muted)]" />
                <span className="text-sm font-semibold text-[var(--text-primary)]">الشركة</span>
              </div>
            </CardHeader>
            <CardContent>
              {company ? (
                <div className="space-y-3">
                  <Link
                    href={`/companies/${company.id}`}
                    className="block font-medium text-[var(--text-primary)] hover:text-[var(--muhide-orange)] transition-colors"
                  >
                    {company.name_ar || company.name_en || company.id}
                  </Link>
                  {company.cr_number && (
                    <div className="text-sm text-[var(--text-secondary)]">س.ت: {company.cr_number}</div>
                  )}
                  {company.city && (
                    <div className="text-sm text-[var(--text-secondary)]">المدينة: {company.city}</div>
                  )}
                  <Link
                    href={`/companies/${company.id}/360`}
                    className="inline-flex items-center gap-1 text-xs text-[var(--muhide-orange)] hover:underline"
                  >
                    <Building2 className="h-3 w-3" /> عرض 360
                  </Link>
                </div>
              ) : (
                <p className="text-sm text-[var(--text-muted)]">معلومات الشركة من Company Intelligence</p>
              )}
            </CardContent>
          </Card>

          {/* Deal Health */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-[var(--text-muted)]" />
                <span className="text-sm font-semibold text-[var(--text-primary)]">صحة الفرصة</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">المرحلة</span>
                  <span className="text-sm font-medium text-[var(--text-primary)]">{stageLabels[opportunity.stage] || opportunity.stage}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">الاحتمالية</span>
                  <span className="text-sm font-medium text-[var(--text-primary)]">{Math.round(opportunity.probability * 100)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">القيمة</span>
                  <span className="text-sm font-medium text-[var(--text-primary)]">{opportunity.value.toLocaleString()} {opportunity.currency}</span>
                </div>
                {opportunity.expectedCloseDate && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-[var(--text-secondary)]">تاريخ الإغلاق المتوقع</span>
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      {new Date(opportunity.expectedCloseDate).toLocaleDateString("ar-SA")}
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-secondary)]">الحالة</span>
                  <span className={cn(
                    "text-sm font-medium",
                    opportunity.health === "healthy" && "text-success-600",
                    opportunity.health === "at_risk" && "text-warning-600",
                    opportunity.health === "critical" && "text-danger-600"
                  )}>
                    {opportunity.health === "healthy" && <CheckCircle className="h-4 w-4 inline mr-1" />}
                    {opportunity.health === "at_risk" && <AlertTriangle className="h-4 w-4 inline mr-1" />}
                    {opportunity.health === "critical" && <XCircle className="h-4 w-4 inline mr-1" />}
                    {healthLabel[opportunity.health] || opportunity.health}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
