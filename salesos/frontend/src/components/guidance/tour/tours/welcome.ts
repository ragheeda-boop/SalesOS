import type { TourStep } from "../TourStep"

export const WELCOME_TOUR: TourStep[] = [
  {
    target: "",
    title: "مرحباً بك في SalesOS",
    description: "منصة ذكاء الأعمال المتكاملة التي تساعدك على اكتشاف الشركات، إدارة الصفقات، وأتمتة سير العمل.",
    position: "center",
  },
  {
    target: "[data-tour='pipeline']",
    title: "خط أنابيب المبيعات",
    description: "تابع صفقاتك في لوحة كانبان، انقل الصفقات بين المراحل، وأغلق الصفقات بالفوز أو الخسارة.",
    position: "bottom",
  },
  {
    target: "[data-tour='nba']",
    title: "التوصيات الذكية",
    description: "احصل على توصيات مدعومة بالذكاء الاصطناعي لأفضل إجراء تالي بناءً على بيانات شركاتك.",
    position: "top",
  },
  {
    target: "[data-tour='search']",
    title: "البحث في كل شيء",
    description: "ابحث عن الشركات، جهات الاتصال، والفرص بسرعة من شريط البحث الذكي.",
    position: "bottom",
  },
  {
    target: "",
    title: "ابدأ رحلتك",
    description: "أنشئ فرصة جديدة وابدأ في استكشاف قوة SalesOS. يمكنك إعادة هذه الجولة من قائمة المساعدة.",
    position: "center",
  },
]
