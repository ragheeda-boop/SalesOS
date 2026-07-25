import { Spinner } from"@salesos/ui"

export default function DashboardLoading() {
 return (
 <div className="flex items-center justify-center min-h-[400px]">
 <Spinner className="h-8 w-8 text-[var(--muhide-orange)]" />
 </div>
 )
}
