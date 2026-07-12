import { render, screen, fireEvent } from "@testing-library/react"
import { HealthDashboard } from "../HealthDashboard"
import type { AdminDetailedHealth, AdminHealthHistoryEntry } from "@/lib/api"

const healthyHealth: AdminDetailedHealth = {
  overall_status: "healthy",
  uptime_seconds: 259200,
  components: [
    { component: "PostgreSQL", status: "healthy", latency_ms: 12, last_check: "2026-07-12T10:00:00Z", details: null },
    { component: "Redis", status: "healthy", latency_ms: 3, last_check: "2026-07-12T10:00:00Z", details: null },
  ],
}

const unhealthyHealth: AdminDetailedHealth = {
  overall_status: "unhealthy",
  uptime_seconds: 86400,
  components: [
    { component: "PostgreSQL", status: "healthy", latency_ms: 12, last_check: "2026-07-12T10:00:00Z", details: null },
    { component: "Neo4j", status: "unhealthy", latency_ms: null, last_check: "2026-07-12T10:00:00Z", details: "Connection refused" },
  ],
}

const sampleHistory: AdminHealthHistoryEntry[] = [
  { timestamp: "2026-07-12T09:00:00Z", overall_status: "healthy", components: { PostgreSQL: "healthy", Redis: "healthy" } },
  { timestamp: "2026-07-12T09:30:00Z", overall_status: "unhealthy", components: { PostgreSQL: "healthy", Neo4j: "unhealthy" } },
]

jest.mock("@/lib/hooks/adminQueries", () => ({
  useAdminDetailedHealth: jest.fn(),
  useAdminHealthHistory: jest.fn(),
}))

import { useAdminDetailedHealth, useAdminHealthHistory } from "@/lib/hooks/adminQueries"

const mockUseHealth = useAdminDetailedHealth as jest.Mock
const mockUseHistory = useAdminHealthHistory as jest.Mock

function setup(health: AdminDetailedHealth | null = healthyHealth, history: AdminHealthHistoryEntry[] = sampleHistory, loading = false) {
  mockUseHealth.mockReturnValue({ data: health, isLoading: loading })
  mockUseHistory.mockReturnValue({ data: history, isLoading: loading })
}

describe("HealthDashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setup()
  })

  it("renders title", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("صحة النظام")).toBeInTheDocument()
  })

  it("shows loading state", () => {
    setup(null, [], true)
    render(<HealthDashboard />)
    expect(screen.getByText("جاري التحميل...")).toBeInTheDocument()
  })

  it("shows healthy status indicator when system healthy", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("النظام سليم")).toBeInTheDocument()
  })

  it("shows unhealthy status indicator when system unhealthy", () => {
    setup(unhealthyHealth)
    render(<HealthDashboard />)
    expect(screen.getByText("يوجد خلل")).toBeInTheDocument()
  })

  it("displays uptime in days", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("3d")).toBeInTheDocument()
  })

  it("displays components count", () => {
    render(<HealthDashboard />)
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1)
  })

  it("displays healthy components count", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("سليمة")).toBeInTheDocument()
  })

  it("displays history count", () => {
    render(<HealthDashboard />)
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1)
  })

  it("renders component cards with names", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument()
    expect(screen.getByText("Redis")).toBeInTheDocument()
  })

  it("shows healthy status badge for healthy components", () => {
    render(<HealthDashboard />)
    const badges = screen.getAllByText("healthy")
    expect(badges.length).toBeGreaterThanOrEqual(1)
  })

  it("shows unhealthy status badge for unhealthy components", () => {
    setup(unhealthyHealth)
    render(<HealthDashboard />)
    const unhealthyBadges = screen.getAllByText("unhealthy")
    expect(unhealthyBadges.length).toBeGreaterThanOrEqual(1)
  })

  it("displays component latency", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("الاستجابة: 12ms")).toBeInTheDocument()
    expect(screen.getByText("الاستجابة: 3ms")).toBeInTheDocument()
  })

  it("displays component details when present", () => {
    setup(unhealthyHealth)
    render(<HealthDashboard />)
    expect(screen.getByText("Connection refused")).toBeInTheDocument()
  })

  it("renders health history section", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("تاريخ الصحة (آخر 24 ساعة)")).toBeInTheDocument()
  })

  it("renders history entries with status badges", () => {
    render(<HealthDashboard />)
    const healthyBadges = screen.getAllByText("healthy")
    expect(healthyBadges.length).toBeGreaterThanOrEqual(2)
    const unhealthyBadges = screen.getAllByText("unhealthy")
    expect(unhealthyBadges.length).toBeGreaterThanOrEqual(1)
  })

  it("shows component status in history entries", () => {
    render(<HealthDashboard />)
    expect(screen.getAllByText("PostgreSQL: healthy").length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText("Redis: healthy")).toBeInTheDocument()
    expect(screen.getByText("Neo4j: unhealthy")).toBeInTheDocument()
  })

  it("shows empty history message when no history", () => {
    setup(healthyHealth, [])
    render(<HealthDashboard />)
    expect(screen.getByText("لا توجد بيانات تاريخية")).toBeInTheDocument()
  })

  it("shows component status heading", () => {
    render(<HealthDashboard />)
    expect(screen.getByText("حالة المكونات")).toBeInTheDocument()
  })

  it("handles null health data gracefully", () => {
    setup(null)
    render(<HealthDashboard />)
    expect(screen.getByText("صحة النظام")).toBeInTheDocument()
    expect(screen.getByText("0d")).toBeInTheDocument()
  })

  it("handles null history gracefully", () => {
    setup(healthyHealth, [])
    render(<HealthDashboard />)
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(1)
  })
})
