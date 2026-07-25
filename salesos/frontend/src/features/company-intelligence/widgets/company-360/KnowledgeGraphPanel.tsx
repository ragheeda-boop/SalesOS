"use client"

import { useMemo } from"react"
import Link from"next/link"
import { useCompany360 } from"@/lib/hooks/company360Queries"
import { Card, CardContent, CardHeader, cn, Skeleton, EmptyState } from"@salesos/ui"
import { Share2, ExternalLink, Building2, Users, ArrowLeft } from"lucide-react"

interface KnowledgeGraphPanelProps {
 companyId: string
 company360?: ReturnType<typeof useCompany360>["data"] | null
}

type RelationshipType ="competitor" |"partner" |"subsidiary" |"parent" |"supplier" |"customer"

const RELATION_COLORS: Record<RelationshipType, string> = {
 competitor:"bg-[var(--color-danger-bg)] text-[var(--color-danger)] border-[var(--color-danger-border)]",
 partner:"bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]",
 subsidiary:"bg-[var(--color-info-bg)] text-[var(--color-info)] border-[var(--color-info-border)]",
 parent:"bg-[var(--color-warning-bg)] text-[var(--color-warning)] border-[var(--color-warning-border)]",
 supplier:"bg-[var(--color-purple-bg)] text-[var(--color-purple)] border-[var(--color-purple-border)]",
 customer:"bg-[var(--color-orange-bg)] text-[var(--color-orange)] border-[var(--color-orange-border)]",
}

const RELATION_LABELS: Record<RelationshipType, string> = {
 competitor:"منافس",
 partner:"شريك",
 subsidiary:"شركة تابعة",
 parent:"شركة أم",
 supplier:"مورد",
 customer:"عميل",
}

function StrengthBar({ value }: { value: number }) {
 const width = Math.round(value * 100)
 const color = value >= 0.7 ?"bg-[var(--color-success)]" : value >= 0.4 ?"bg-[var(--color-warning)]" :"bg-[var(--color-danger)]"
 return (
 <div className="flex items-center gap-2">
 <div className="h-1.5 flex-1 rounded-full bg-[var(--bg-tertiary)]">
 <div className={cn("h-1.5 rounded-full transition-all", color)} style={{ width: `${width}%` }} />
 </div>
 <span className="text-[10px] font-medium text-[var(--text-muted)] w-8 text-left">{Math.round(value * 100)}%</span>
 </div>
 )
}

export function KnowledgeGraphPanel({ companyId, company360: externalCompany360 }: KnowledgeGraphPanelProps) {
 const { data: fetchedCompany360, isLoading, isError } = useCompany360(companyId)
 const company360 = externalCompany360 ?? fetchedCompany360

 const relatedEntities = useMemo(() => {
 if (!company360?.related_entities) return []
 return company360.related_entities.map((e: Record<string, unknown>) => ({
 id: e.id as string,
 name: e.name as string,
 type: (e.type as RelationshipType) ||"partner",
 confidence: (e.confidence as number) || 0.5,
 }))
 }, [company360])

 if (isLoading) {
 return (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
 <Share2 className="h-5 w-5 text-[var(--text-muted)]" />
 <span className="text-sm font-semibold text-[var(--text-primary)]">شبكة العلاقات</span>
 </div>
 </CardHeader>
 <CardContent>
 <div className="space-y-4">
 {Array.from({ length: 4 }).map((_, i) => (
 <Skeleton key={i} variant="card" />
 ))}
 </div>
 </CardContent>
 </Card>
 )
 }

 if (isError) {
 return (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
 <Share2 className="h-5 w-5 text-[var(--text-muted)]" />
 <span className="text-sm font-semibold text-[var(--text-primary)]">شبكة العلاقات</span>
 </div>
 </CardHeader>
 <CardContent>
 <EmptyState icon={<Share2 className="h-10 w-10" />} title="فشل تحميل العلاقات" description="تعذر تحميل بيانات شبكة العلاقات" />
 </CardContent>
 </Card>
 )
 }

 if (relatedEntities.length === 0) {
 return (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
 <Share2 className="h-5 w-5 text-[var(--text-muted)]" />
 <span className="text-sm font-semibold text-[var(--text-primary)]">شبكة العلاقات</span>
 </div>
 </CardHeader>
 <CardContent>
 <EmptyState icon={<Share2 className="h-10 w-10" />} title="لا توجد علاقات" description="لم يتم العثور على علاقات لهذه الشركة" />
 </CardContent>
 </Card>
 )
 }

 const grouped = relatedEntities.reduce<Record<string, typeof relatedEntities>>((acc, e) => {
 const key = e.type ||"partner"
 if (!acc[key]) acc[key] = []
 acc[key].push(e)
 return acc
 }, {})

 return (
 <Card>
 <CardHeader>
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <Share2 className="h-5 w-5 text-[var(--text-muted)]" />
 <span className="text-sm font-semibold text-[var(--text-primary)]">شبكة العلاقات</span>
 </div>
 <span className="text-xs text-[var(--text-muted)]">{relatedEntities.length} كيان</span>
 </div>
 </CardHeader>
 <CardContent>
 <div className="space-y-5">
 {Object.entries(grouped).map(([type, entities]) => (
 <div key={type}>
 <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
 {RELATION_LABELS[type as RelationshipType] || type}
 </h4>
 <div className="space-y-2">
 {entities.map((entity) => (
 <Link
 key={entity.id}
 href={`/companies/${entity.id}`}
 className={cn(
"group flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50",
 RELATION_COLORS[entity.type as RelationshipType] ||"border-[var(--border-default)]"
 )}
 >
 <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--bg-primary)]">
 <Building2 className="h-4 w-4" />
 </div>
 <div className="min-w-0 flex-1">
 <p className="truncate text-sm font-medium text-[var(--text-primary)]">
 {entity.name}
 </p>
 <StrengthBar value={entity.confidence} />
 </div>
 <ExternalLink className="h-4 w-4 shrink-0 text-[var(--text-disabled)] opacity-0 transition-opacity group-hover:opacity-100" />
 </Link>
 ))}
 </div>
 </div>
 ))}
 </div>
 </CardContent>
 </Card>
 )
}
