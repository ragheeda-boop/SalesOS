import type { TourStep } from "../TourStep"

export const PIPELINE_TOUR: TourStep[] = [
  {
    target: "[data-tour='pipeline']",
    title: "نظرة عامة على خط الأنابيب",
    description: "هذا هو مركز إدارة صفقاتك. يمكنك رؤية جميع الفرص التجارية في مكان واحد.",
    position: "bottom",
  },
  {
    target: "[data-tour='kanban-columns']",
    title: "عرض كانبان",
    description: "الأعمدة تمثل مراحل البيع المختلفة. اسحب الصفقات بين الأعمدة لتحديث مرحلتها.",
    position: "top",
  },
  {
    target: "[data-tour='deal-card']",
    title: "بطاقات الصفقات",
    description: "كل بطاقة تمثل فرصة. تعرض اسم الشركة، قيمة الصفقة، والمرحلة الحالية.",
    position: "top",
  },
  {
    target: "[data-tour='forecast']",
    title: "التوقعات",
    description: "بطاقات التوقعات تظهر إجمالي قيمة الصفقات في كل مرحلة لتساعدك على التنبؤ بالإيرادات.",
    position: "bottom",
  },
  {
    target: "[data-tour='pipeline']",
    title: "تحريك الصفقات",
    description: "اسحب وأفلت الصفقات بين المراحل. عند الوصول إلى المرحلة النهائية، يمكنك إغلاق الصفقة بالفوز أو الخسارة.",
    position: "bottom",
  },
]
