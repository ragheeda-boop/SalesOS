"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { Breadcrumbs, Card, CardContent, CardHeader, Skeleton, EmptyState, Badge } from "@salesos/ui";
import { useTranslation } from "@/lib/i18n";
import { useTenant } from "@/lib/hooks/useTenant";
import {
  User, Building2, Handshake, Mail, Phone, MapPin,
  Briefcase, Calendar, ArrowLeft, Trash2, Pencil
} from "lucide-react";

interface ContactDetail {
  id: string;
  name: string;
  name_ar?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  position?: string;
  position_ar?: string;
  department?: string;
  company_id?: string;
  is_primary?: boolean;
  source?: string;
  tags?: string[];
  confidence_score?: number;
}

interface CompanySnapshot {
  id: string;
  name_ar?: string;
  name_en?: string;
  cr_number?: string;
  city?: string;
  status?: string;
}

interface LinkedOpportunity {
  id: string;
  opportunity_id: string;
  contact_id: string;
  role?: string;
  is_primary?: boolean;
  opp_name?: string;
  opp_stage?: string;
  opp_value?: number;
}

export default function ContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const { tenantId } = useTenant();

  const [contact, setContact] = useState<ContactDetail | null>(null);
  const [company, setCompany] = useState<CompanySnapshot | null>(null);
  const [opportunities, setOpportunities] = useState<LinkedOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/api/v1/contacts/${id}`, {
          headers: { "X-Tenant-Id": tenantId }
        });
        setContact(data);

        if (data.company_id) {
          try {
            const cr = await api.get(`/api/v1/companies/${data.company_id}`, {
              headers: { "X-Tenant-Id": tenantId }
            });
            setCompany(cr.data);
          } catch { /* best-effort */ }
        }

        // Load linked opportunities via ADR-030
        try {
          const or = await api.get("/api/v1/opportunity-contacts", {
            params: { contact_id: id },
            headers: { "X-Tenant-Id": tenantId }
          });
          const items = or.data?.items || or.data || [];
          const enriched: LinkedOpportunity[] = [];
          for (const oc of items) {
            let oppDetail: Record<string, unknown> = {};
            try {
              const oppRes = await api.get(`/api/v1/opportunities/${oc.opportunity_id}`, {
                headers: { "X-Tenant-Id": tenantId }
              });
              oppDetail = oppRes.data || {};
            } catch { /* best-effort */ }
            enriched.push({
              ...oc,
              opp_name: (oppDetail.name as string) || oc.opportunity_id,
              opp_stage: (oppDetail.stage as string),
              opp_value: (oppDetail.value as number),
            });
          }
          setOpportunities(enriched);
        } catch { /* optional */ }
      } catch { /* handled by empty state */ }
      finally { setLoading(false); }
    };
    load();
  }, [id, tenantId]);

  const handleDelete = async () => {
    if (!confirm("هل أنت متأكد من حذف جهة الاتصال هذه؟")) return;
    setDeleting(true);
    try {
      await api.delete(`/api/v1/contacts/${id}`, {
        headers: { "X-Tenant-Id": tenantId }
      });
      router.push("/contacts");
    } catch {
      alert("فشل حذف جهة الاتصال");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="py-20">
        <EmptyState
          icon={<User className="h-12 w-12" />}
          title="جهة الاتصال غير موجودة"
          description="لم يتم العثور على جهة الاتصال المطلوبة"
          action={{ label: "العودة للقائمة", onClick: () => router.push("/contacts") }}
        />
      </div>
    );
  }

  const stageLabels: Record<string, string> = {
    prospecting: "استكشاف", qualification: "تأهيل",
    proposal: "عرض", negotiation: "تفاوض",
    closed_won: "فوز", closed_lost: "خسارة",
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: t("nav.contacts"), href: "/contacts" },
          { label: contact.name, href: undefined },
        ]}
      />

      {/* Header */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <div className="flex flex-wrap items-center gap-4 px-6 py-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
            <User className="h-7 w-7" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-[var(--text-primary)]">{contact.name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
              {contact.position && (
                <span className="flex items-center gap-1">
                  <Briefcase className="h-3.5 w-3.5" /> {contact.position}
                </span>
              )}
              {contact.department && (
                <span className="flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5" /> {contact.department}
                </span>
              )}
              {contact.is_primary && <Badge variant="default">أساسي</Badge>}
              {contact.source && <span className="text-xs text-[var(--text-muted)]">المصدر: {contact.source}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/contacts/${id}/edit`}
              className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium hover:bg-[var(--bg-secondary)]"
            >
              <Pencil className="h-3.5 w-3.5" /> تعديل
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="inline-flex items-center gap-1 rounded-lg border border-danger-200 px-3 py-1.5 text-xs font-medium text-danger-600 hover:bg-danger-50 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" /> حذف
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Contact Info */}
        <Card>
          <CardHeader>
            <span className="text-sm font-semibold text-[var(--text-primary)]">معلومات الاتصال</span>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {contact.email && (
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
                  <a href={`mailto:${contact.email}`} className="text-sm text-[var(--text-primary)] hover:text-[var(--muhide-orange)]">{contact.email}</a>
                </div>
              )}
              {contact.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
                  <a href={`tel:${contact.phone}`} className="text-sm text-[var(--text-primary)]">{contact.phone}</a>
                </div>
              )}
              {contact.mobile && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
                  <span className="text-sm text-[var(--text-primary)]">{contact.mobile}</span>
                </div>
              )}
              {contact.position_ar && (
                <div className="flex items-center gap-3">
                  <Briefcase className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
                  <span className="text-sm text-[var(--text-primary)]">{contact.position_ar}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Company */}
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
                  className="block font-medium text-[var(--text-primary)] hover:text-[var(--muhide-orange)]"
                >
                  {company.name_ar || company.name_en}
                </Link>
                {company.cr_number && <div className="text-sm text-[var(--text-secondary)]">س.ت: {company.cr_number}</div>}
                {company.city && <div className="text-sm text-[var(--text-secondary)] flex items-center gap-1"><MapPin className="h-3 w-3" />{company.city}</div>}
                <Link href={`/companies/${company.id}/360`} className="text-xs text-[var(--muhide-orange)] hover:underline">
                  عرض 360
                </Link>
              </div>
            ) : (
              <p className="text-sm text-[var(--text-muted)]">غير مرتبط بشركة</p>
            )}
          </CardContent>
        </Card>

        {/* Opportunities via ADR-030 */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Handshake className="h-5 w-5 text-[var(--text-muted)]" />
              <span className="text-sm font-semibold text-[var(--text-primary)]">الفرص المرتبطة</span>
              {opportunities.length > 0 && (
                <span className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">{opportunities.length}</span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {opportunities.length > 0 ? (
              <div className="space-y-2">
                {opportunities.map((oc) => (
                  <Link
                    key={oc.id}
                    href={`/opportunities/${oc.opportunity_id}`}
                    className="block p-3 rounded-lg border border-[var(--border-default)] hover:bg-[var(--bg-secondary)]"
                  >
                    <div className="font-medium text-[var(--text-primary)]">{oc.opp_name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      {oc.opp_stage && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                          {stageLabels[oc.opp_stage] || oc.opp_stage}
                        </span>
                      )}
                      {oc.opp_value != null && (
                        <span className="text-xs font-medium text-[var(--text-primary)]">
                          {oc.opp_value.toLocaleString()} ر.س
                        </span>
                      )}
                      {oc.role && <span className="text-[10px] text-[var(--text-muted)]">{oc.role}</span>}
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[var(--text-muted)] py-4 text-center">لا توجد فرص مرتبطة</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
