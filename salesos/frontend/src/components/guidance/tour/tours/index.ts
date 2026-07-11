import { WELCOME_TOUR } from "./welcome"
import { PIPELINE_TOUR } from "./pipeline"
import { NBA_TOUR } from "./nba"
import { WORKFLOW_TOUR } from "./workflow"
import { RAG_TOUR } from "./rag"
import type { TourStep } from "../TourStep"

export const TOUR_REGISTRY: Record<string, TourStep[]> = {
  "welcome": WELCOME_TOUR,
  "pipeline": PIPELINE_TOUR,
  "nba": NBA_TOUR,
  "workflow": WORKFLOW_TOUR,
  "rag": RAG_TOUR,
}

export const TOUR_LABELS: Record<string, string> = {
  welcome: "جولة ترحيبية",
  pipeline: "جولة خط الأنابيب",
  nba: "جولة التوصيات الذكية",
  workflow: "جولة الأتمتة",
  rag: "جولة الاستخبارات المعرفية",
}

export { WELCOME_TOUR, PIPELINE_TOUR, NBA_TOUR, WORKFLOW_TOUR, RAG_TOUR }
