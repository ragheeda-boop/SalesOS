"use client"

import { useState } from "react"
import { Button, Badge, Card, Spinner } from "@salesos/ui"
import { RefreshCw, AlertTriangle, CheckCircle, Clock, Play } from "lucide-react"
import { useAdminJobs, useAdminJobDetail, useRetryAdminJob } from "@/lib/hooks/adminQueries"
import { AdminJob } from "@/lib/api"

export function JobList() {
  const [statusFilter, setStatusFilter] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [selectedJob, setSelectedJob] = useState<string | null>(null)

  const { data: jobs, isLoading } = useAdminJobs({
    status: statusFilter || undefined,
    job_type: typeFilter || undefined,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">الوظائف الخلفية</h2>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setSelectedJob(null) }}
          className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value="">كل الحالات</option>
          <option value="pending">قيد الانتظار</option>
          <option value="running">قيد التشغيل</option>
          <option value="completed">مكتملة</option>
          <option value="failed">فاشلة</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setSelectedJob(null) }}
          className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value="">كل الأنواع</option>
          <option value="data_ingestion">استيراد بيانات</option>
          <option value="entity_resolution">حل الكيانات</option>
          <option value="email_enrichment">إثراء البريد</option>
          <option value="report_generation">توليد تقارير</option>
          <option value="sync_crm">مزامنة CRM</option>
        </select>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-neutral-500"><Spinner /></div>
      ) : !jobs?.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا توجد وظائف</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-2">
            {jobs.map((job: AdminJob) => (
              <button
                key={job.id}
                onClick={() => setSelectedJob(selectedJob === job.id ? null : job.id)}
                className={`w-full text-right flex items-center justify-between p-3 rounded-lg border transition ${
                  selectedJob === job.id ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5" : "border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                }`}
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={job.status} />
                  <div>
                    <p className="font-medium text-sm">{job.type}</p>
                    <p className="text-xs text-neutral-500">{job.id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={job.status === "completed" ? "success" : job.status === "failed" ? "danger" : job.status === "running" ? "warning" : "default"}>
                    {job.status}
                  </Badge>
                  {job.status === "running" && <span className="text-xs text-neutral-400">{job.progress}%</span>}
                </div>
              </button>
            ))}
          </div>

          <div>
            {selectedJob ? (
              <JobDetailPanel jobId={selectedJob} />
            ) : (
              <Card className="p-6 text-center text-neutral-500">
                <RefreshCw className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>اختر وظيفة لعرض التفاصيل</p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed": return <CheckCircle className="h-5 w-5 text-success-500" />
    case "failed": return <AlertTriangle className="h-5 w-5 text-danger-500" />
    case "running": return <RefreshCw className="h-5 w-5 text-amber-500 animate-spin" />
    default: return <Clock className="h-5 w-5 text-neutral-400" />
  }
}

function JobDetailPanel({ jobId }: { jobId: string }) {
  const { data: job, isLoading } = useAdminJobDetail(jobId)
  const retryMutation = useRetryAdminJob()

  if (isLoading) return <Card className="p-4"><Spinner /></Card>
  if (!job) return null

  return (
    <Card className="p-4 space-y-4">
      <div>
        <h3 className="font-semibold">{job.type}</h3>
        <p className="text-xs text-neutral-500 font-mono">{job.id}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div><span className="text-neutral-500">الحالة:</span> <Badge>{job.status}</Badge></div>
        <div><span className="text-neutral-500">التقدم:</span> {job.progress}%</div>
        <div><span className="text-neutral-500">المحاولات:</span> {job.retry_count}/{job.max_retries}</div>
        {job.tenant_id && <div><span className="text-neutral-500">العميل:</span> {job.tenant_id}</div>}
      </div>

      {job.error_message && (
        <div className="bg-danger-50 dark:bg-danger-900/20 p-3 rounded text-xs text-danger-700 dark:text-danger-300">
          {job.error_message}
        </div>
      )}

      {job.status === "failed" && (
        <Button onClick={() => retryMutation.mutate(jobId)} disabled={retryMutation.isPending} className="gap-2 w-full">
          <Play className="h-4 w-4" />
          إعادة المحاولة
        </Button>
      )}

      {job.logs && job.logs.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">سجل التنفيذ</h4>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {job.logs.map((log: { level: string; message: string; timestamp: string }, i: number) => (
              <div key={i} className={`text-xs p-1.5 rounded ${log.level === "ERROR" ? "bg-danger-50 dark:bg-danger-900/20 text-danger-600" : "bg-neutral-50 dark:bg-neutral-800"}`}>
                <span className="font-mono text-neutral-400">{new Date(log.timestamp).toLocaleTimeString("ar-SA")}</span>
                <span className="mx-1">[{log.level}]</span>
                <span>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
