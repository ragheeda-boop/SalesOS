import type { TourStep } from "../TourStep"

export const RAG_TOUR: TourStep[] = [
  {
    target: "[data-tour='rag-workspace']",
    title: "الاستخبارات المعرفية",
    description: "اسأل أسئلة عن شركاتك واحصل على إجابات مدعومة بالمستندات التي قمت برفعها.",
    position: "bottom",
  },
  {
    target: "[data-tour='rag-chat']",
    title: "طرح الأسئلة",
    description: "اكتب سؤالك بالعربية أو الإنجليزية عن أي شركة. النظام يبحث في المستندات المرفوعة.",
    position: "top",
  },
  {
    target: "[data-tour='rag-documents']",
    title: "إدارة المستندات",
    description: "ارفع ملفات الشركات (PDF, DOCX, TXT) لتكون قاعدة المعرفة الخاصة بك.",
    position: "bottom",
  },
  {
    target: "[data-tour='rag-citations']",
    title: "الاستشهادات",
    description: "كل إجابة تأتي مع استشهادات من المصدر الأصلي. اضغط على المرجع للاطلاع على التفاصيل.",
    position: "top",
  },
]
