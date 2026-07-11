import type { TourStep } from "../TourStep"

export const NBA_TOUR: TourStep[] = [
  {
    target: "[data-tour='nba']",
    title: "أفضل الإجراءات التالية",
    description: "تعرض هذه الواجهة الإجراءات المقترحة التي يجب عليك اتخاذها بناءً على تحليل الذكاء الاصطناعي.",
    position: "top",
  },
  {
    target: "[data-tour='nba-recommendation']",
    title: "التوصيات",
    description: "كل توصية تحتوي على إجراء مقترح، القيمة المتوقعة، والأولوية.",
    position: "bottom",
  },
  {
    target: "[data-tour='nba-actions']",
    title: "قبول أو رفض",
    description: "يمكنك قبول التوصية لتنفيذ الإجراء، أو رفضها مع توضيح السبب لتحسين التوصيات المستقبلية.",
    position: "top",
  },
  {
    target: "[data-tour='nba-evidence']",
    title: "سلسلة الأدلة",
    description: "كل توصية مدعومة بأدلة من بيانات شركاتك. اضغط على 'لماذا' لمعرفة مصدر التوصية.",
    position: "bottom",
  },
]
