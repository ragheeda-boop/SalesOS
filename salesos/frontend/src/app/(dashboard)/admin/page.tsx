"use client"

import { useState, useCallback } from "react"
import { useAdminHealth, useAdminMetrics, useGoldenRecords, useConflicts, useDlq, useDlqStats, useRetryDlq, usePurgeDlq } from "@/lib/hooks/adminQueries"
import { Input, Button, Badge, Spinner, Card, cn, Tabs, TabsList, Tab, TabsPanel } from "@salesos/ui"
import { BarChart, PieChart, MetricCard } from "@salesos/charts"
import { Activity, Database, GitMerge, AlertTriangle, RefreshCw, CheckCircle, XCircle, TrendingUp, BarChart3, PieChart as PieIcon } from "lucide-react"

export default function AdminPage() {
  return (
    <div className="p-6 space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">لوحة الإدارة</h1>
      </div>

      <Tabs defaultValue="pipeline">
        <TabsList>
          <Tab value="pipeline">خط أنابيب البيانات</Tab>
          <Tab value="golden-records">السجلات الذهبية</Tab>
          <Tab value="conflicts">تضاربات الدمج</Tab>
          <Tab value="dlq">قائمة الانتظار الميتة</Tab>
        </TabsList>

        <TabsPanel value="pipeline">
          <PipelineMonitor />
        </TabsPanel>

        <TabsPanel value="golden-records">
          <GoldenRecordsView />
        </TabsPanel>

        <TabsPanel value="conflicts">
          <ConflictsView />
        </TabsPanel>

        <TabsPanel value="dlq">
          <DlqView />
        </TabsPanel>
      </Tabs>
    </div>
  )
}

function PipelineMonitor() {
  const { data: health, isLoading: healthLoading } = useAdminHealth()
  const { data: metricsRaw, isLoading: metricsLoading } = useAdminMetrics()
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = useCallback(() => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 1000)
  }, [])

  if (healthLoading || metricsLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  const pipeline = health?.pipeline
  const isRunning = pipeline && "last_run_at" in pipeline && pipeline.last_run_at

  return (
    <div className="space-y-6 mt-4">
      <div className="flex items-center gap-2">
        <Button onClick={handleRefresh} className="gap-2">
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          تحديث
        </Button>
      </div>

      {pipeline && "status" in pipeline && pipeline.status === "not_initialized" ? (
        <Card className="p-6 text-center text-neutral-500">
          <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>خط أنابيب البيانات غير مهيأ</p>
        </Card>
      ) : pipeline && "records_ingested" in pipeline ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Activity} label="السجلات المستوردة" value={pipeline.records_ingested} color="blue" />
            <StatCard icon={CheckCircle} label="الصالحة" value={pipeline.total_valid} color="green" />
            <StatCard icon={AlertTriangle} label="الأخطاء" value={pipeline.total_errors} color="red" />
            <StatCard icon={GitMerge} label="السجلات الذهبية" value={pipeline.golden_records_created} color="purple" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Database} label="الشركات المزامنة" value={pipeline.companies_synced} color="indigo" />
            <StatCard icon={Database} label="التضمينات المخزنة" value={pipeline.embeddings_stored} color="teal" />
            <StatCard icon={Activity} label="ميزات محسوبة" value={pipeline.features_computed} color="orange" />
            <StatCard icon={Activity} label="مدد الرسم البياني" value={pipeline.kg_triples_created} color="pink" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {pipeline.stage_durations_ms && Object.keys(pipeline.stage_durations_ms).length > 0 && (
              <Card className="p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  متوسط أوقات المراحل (مللي ثانية)
                </h3>
                <BarChart
                  data={Object.entries(pipeline.stage_durations_ms).map(([stage, ms]) => ({
                    label: stage,
                    value: ms as number,
                  }))}
                  height={250}
                />
              </Card>
            )}

            {pipeline.errors_by_stage && Object.keys(pipeline.errors_by_stage).length > 0 && (
              <Card className="p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <PieIcon className="h-4 w-4" />
                  الأخطاء حسب المرحلة
                </h3>
                <PieChart
                  data={Object.entries(pipeline.errors_by_stage).map(([stage, count]) => ({
                    label: stage,
                    value: count as number,
                  }))}
                />
              </Card>
            )}
          </div>

          {/* Summary MetricCards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="إجمالي السجلات" value={String(pipeline.records_ingested)} />
            <MetricCard label="الصالحة" value={String(pipeline.total_valid)} />
            <MetricCard label="السجلات الذهبية" value={String(pipeline.golden_records_created)} />
            <MetricCard label="الشركات المزامنة" value={String(pipeline.companies_synced)} />
          </div>

          {/* Stage durations detail bars */}
          {pipeline.stage_durations_ms && Object.keys(pipeline.stage_durations_ms).length > 0 && (
            <Card className="p-4">
              <h3 className="font-semibold mb-3">تفاصيل أوقات المراحل</h3>
              <div className="space-y-2">
                {Object.entries(pipeline.stage_durations_ms).map(([stage, ms]) => (
                  <div key={stage} className="flex items-center gap-3">
                    <span className="w-36 text-sm text-neutral-600 dark:text-neutral-400">{stage}</span>
                    <div className="flex-1 h-4 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[var(--muhide-orange)] rounded-full transition-all"
                        style={{ width: `${Math.min(100, (ms as number) / 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono w-20 text-left">{ms as number}ms</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card className="p-4">
            <h3 className="font-semibold mb-3">حالة الخدمات</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(health?.checks || {}).map(([service, status]) => (
                <div key={service} className="flex items-center gap-2 text-sm">
                  {status === "connected" ? (
                    <CheckCircle className="h-4 w-4 text-success-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-danger-500" />
                  )}
                  <span className="text-neutral-600 dark:text-neutral-400">{service}</span>
                  <span className={cn("font-mono text-xs", status === "connected" ? "text-success-600" : "text-danger-600")}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : null}
    </div>
  )
}

function GoldenRecordsView() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useGoldenRecords({ page, page_size: 20 })

  if (isLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-neutral-500">إجمالي: {data?.total || 0}</p>
      </div>

      {!data?.items?.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا توجد سجلات ذهبية بعد</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-neutral-700 text-right">
                <th className="p-2 font-medium">رقم السجل</th>
                <th className="p-2 font-medium">اسم الشركة</th>
                <th className="p-2 font-medium">رقم CR</th>
                <th className="p-2 font-medium">الحالة</th>
                <th className="p-2 font-medium">درجة الثقة</th>
                <th className="p-2 font-medium">المصادر</th>
                <th className="p-2 font-medium">تاريخ الإنشاء</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((record) => (
                <tr key={record.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                  <td className="p-2 font-mono text-xs" data-label="رقم السجل">{record.id.slice(0, 8)}...</td>
                  <td className="p-2" data-label="اسم الشركة">{record.company_name_ar || "-"}</td>
                  <td className="p-2 font-mono" data-label="رقم CR">{record.cr_number || "-"}</td>
                  <td className="p-2" data-label="الحالة">
                    <Badge variant={record.status === "active" ? "success" : record.status === "merged" ? "warning" : "default"}>
                      {record.status}
                    </Badge>
                  </td>
                  <td className="p-2" data-label="درجة الثقة">{record.confidence_score?.toFixed(2) || "-"}</td>
                  <td className="p-2" data-label="المصادر">{record.source_records}</td>
                  <td className="p-2 text-xs text-neutral-500" data-label="تاريخ الإنشاء">{new Date(record.created_at).toLocaleDateString("ar-SA")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > data.page_size && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>السابق</Button>
          <span className="text-sm px-4">
            صفحة {data.page} من {Math.ceil(data.total / data.page_size)}
          </span>
          <Button disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage((p) => p + 1)}>التالي</Button>
        </div>
      )}
    </div>
  )
}

function ConflictsView() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useConflicts({ page, page_size: 20 })

  if (isLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-neutral-500">إجمالي: {data?.total || 0}</p>
      </div>

      {!data?.items?.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <GitMerge className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا توجد تضاربات — جميع السجلات متناسقة</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-neutral-700 text-right">
                <th className="p-2 font-medium">رقم CR (أ)</th>
                <th className="p-2 font-medium">رقم CR (ب)</th>
                <th className="p-2 font-medium">الحالة</th>
                <th className="p-2 font-medium">السبب</th>
                <th className="p-2 font-medium">تاريخ الإنشاء</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((conflict) => (
                <tr key={conflict.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                  <td className="p-2 font-mono" data-label="رقم CR (أ)">{conflict.cr_number_a}</td>
                  <td className="p-2 font-mono" data-label="رقم CR (ب)">{conflict.cr_number_b}</td>
                  <td className="p-2" data-label="الحالة">
                    <Badge variant={conflict.status === "open" ? "danger" : conflict.status === "resolved" ? "success" : "default"}>
                      {conflict.status}
                    </Badge>
                  </td>
                  <td className="p-2 text-xs" data-label="السبب">{conflict.reason}</td>
                  <td className="p-2 text-xs text-neutral-500" data-label="تاريخ الإنشاء">{new Date(conflict.created_at).toLocaleDateString("ar-SA")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > data.page_size && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>السابق</Button>
          <span className="text-sm px-4">
            صفحة {data.page} من {Math.ceil(data.total / data.page_size)}
          </span>
          <Button disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage((p) => p + 1)}>التالي</Button>
        </div>
      )}
    </div>
  )
}

function DlqView() {
  const [page, setPage] = useState(1)
  const [stageFilter, setStageFilter] = useState("")
  const { data, isLoading } = useDlq({ page, page_size: 20, stage: stageFilter || undefined })
  const { data: stats } = useDlqStats()
  const retryMutation = useRetryDlq()
  const purgeMutation = usePurgeDlq()
  const [retryResult, setRetryResult] = useState<string | null>(null)

  const handleRetry = async () => {
    setRetryResult(null)
    const result = await retryMutation.mutateAsync(50)
    setRetryResult(`تمت معالجة ${result.processed}: تم الحل ${result.resolved}, لا يزال فاشلاً ${result.still_failed}`)
  }

  if (isLoading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  const failedByStage = stats?.failed_by_stage || {}
  const hasFailedEntries = Object.keys(failedByStage).length > 0

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center gap-2 flex-wrap">
        {hasFailedEntries && (
          <>
            <Button onClick={handleRetry} className="gap-2" disabled={retryMutation.isPending}>
              <RefreshCw className={cn("h-4 w-4", retryMutation.isPending && "animate-spin")} />
              إعادة محاولة ({Object.values(failedByStage).reduce((a, b) => a + b, 0)})
            </Button>
            <Button onClick={() => purgeMutation.mutate("failed")} variant="danger" className="gap-2" disabled={purgeMutation.isPending}>
              <XCircle className="h-4 w-4" />
              مسح الفاشل
            </Button>
          </>
        )}
        <select
          value={stageFilter}
          onChange={(e) => { setStageFilter(e.target.value); setPage(1) }}
          className="border rounded px-2 py-1 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value="">كل المراحل</option>
          {Object.keys(failedByStage).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {retryResult && (
        <div className="bg-success-50 dark:bg-success-900/20 text-success-700 dark:text-success-300 p-3 rounded-lg text-sm">
          {retryResult}
        </div>
      )}

      {hasFailedEntries && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(failedByStage).map(([stage, count]) => (
            <DlqStatCard key={stage} stage={stage} count={count} />
          ))}
        </div>
      )}

      {!hasFailedEntries && (!data?.items?.length) ? (
        <Card className="p-6 text-center text-neutral-500">
          <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>قائمة الانتظار الميتة فارغة — لا توجد سجلات فاشلة</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm responsive-table">
            <thead>
              <tr className="border-b dark:border-neutral-700 text-right">
                <th className="p-2 font-medium">#</th>
                <th className="p-2 font-medium">المصدر</th>
                <th className="p-2 font-medium">رقم CR</th>
                <th className="p-2 font-medium">المرحلة</th>
                <th className="p-2 font-medium">الخطأ</th>
                <th className="p-2 font-medium">المحاولات</th>
                <th className="p-2 font-medium">الحالة</th>
                <th className="p-2 font-medium">التاريخ</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.map((entry) => (
                <tr key={entry.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                  <td className="p-2 text-xs font-mono" data-label="#">{entry.id}</td>
                  <td className="p-2" data-label="المصدر">{entry.source_slug}</td>
                  <td className="p-2 font-mono" data-label="رقم CR">{entry.cr_number || "-"}</td>
                  <td className="p-2" data-label="المرحلة">
                    <Badge variant="warning">{entry.stage}</Badge>
                  </td>
                  <td className="p-2 text-xs" data-label="الخطأ" title={entry.error_message}>
                    {entry.error_message.slice(0, 80)}...
                  </td>
                  <td className="p-2" data-label="المحاولات">{entry.retry_count}/{entry.max_retries}</td>
                  <td className="p-2" data-label="الحالة">
                    <Badge variant={entry.status === "failed" ? "danger" : "success"}>
                      {entry.status}
                    </Badge>
                  </td>
                  <td className="p-2 text-xs text-neutral-500" data-label="التاريخ">{new Date(entry.created_at).toLocaleString("ar-SA")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > data.page_size && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>السابق</Button>
          <span className="text-sm px-4">
            صفحة {data.page} من {Math.ceil(data.total / data.page_size)}
          </span>
          <Button disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage((p) => p + 1)}>التالي</Button>
        </div>
      )}
    </div>
  )
}

function DlqStatCard({ stage, count }: { stage: string; count: number }) {
  return (
    <Card className="px-3 py-2 flex items-center gap-2">
      <AlertTriangle className="h-4 w-4 text-danger-500" />
      <span className="text-sm">{stage}</span>
      <span className="text-sm font-bold text-danger-600">{count}</span>
    </Card>
  )
}

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
  const colorMap: Record<string, string> = {
    blue: "bg-info-50 text-info-600 dark:bg-info-900/30 dark:text-info-400",
    green: "bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400",
    red: "bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
    indigo: "bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400",
    teal: "bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400",
    orange: "bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400",
    pink: "bg-pink-50 text-pink-600 dark:bg-pink-900/30 dark:text-pink-400",
  }

  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div className={cn("rounded-lg p-2", colorMap[color] || colorMap.blue)}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">{label}</p>
          <p className="text-xl font-bold">{value}</p>
        </div>
      </div>
    </Card>
  )
}
