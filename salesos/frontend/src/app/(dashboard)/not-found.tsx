import Link from "next/link"

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <h1 className="text-6xl font-bold text-neutral-200 dark:text-neutral-700">404</h1>
      <p className="mt-4 text-neutral-500">Page not found</p>
      <Link
        href="/dashboard"
        className="mt-4 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90"
      >
        Back to Dashboard
      </Link>
    </div>
  )
}
