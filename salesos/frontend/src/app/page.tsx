import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center max-w-2xl">
        <h1 className="text-4xl font-bold mb-4">
          SalesOS
        </h1>
        <p className="text-xl text-[var(--muted-foreground)] mb-8">
          منصة ذكاء الأعمال للمؤسسات
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-[var(--muhide-orange)] text-white rounded-lg hover:bg-orange-700 transition"
          >
            تسجيل الدخول
          </Link>
          <Link
            href="/register"
            className="px-6 py-3 border border-[var(--border)] rounded-lg hover:bg-[var(--muted)] transition"
          >
            إنشاء حساب
          </Link>
        </div>
      </div>
    </main>
  );
}
