import type { TourStep } from "../TourStep"

export const WORKFLOW_TOUR: TourStep[] = [
  {
    target: "[data-tour='workflow-workspace']",
    title: "الأتمتة",
    description: "منصة الأتمتة تسمح لك ببناء وتشغيل سير عمل ذكي بدون كتابة كود.",
    position: "bottom",
  },
  {
    target: "[data-tour='workflow-list']",
    title: "سير العمل الخاص بك",
    description: "هذه قائمة بكل سير العمل التي قمت بإنشائها. يمكنك تفعيلها، إيقافها، أو تعديلها.",
    position: "top",
  },
  {
    target: "[data-tour='workflow-builder']",
    title: "بناء سير العمل",
    description: "استخدم منشئ الخطوات لبناء سير العمل. أضف مشغلات، إجراءات، وشروط بسهولة.",
    position: "top",
  },
  {
    target: "[data-tour='workflow-templates']",
    title: "القوالب الجاهزة",
    description: "ابدأ بسرعة مع قوالب مبنية مسبقاً لتغطية حالات الاستخدام الشائعة.",
    position: "bottom",
  },
  {
    target: "[data-tour='workflow-execution']",
    title: "التنفيذ",
    description: "عند تشغيل سير العمل، يمكنك متابعة حالة التنفيذ وسجل العمليات في الوقت الفعلي.",
    position: "top",
  },
]
