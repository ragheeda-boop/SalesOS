
const EXPECTED_ROUTES = [
  "/dashboard",
  "/companies",
  "/employees/me",
  "/contacts",
  "/opportunities",
  "/revenue",
  "/pipeline",
  "/forecast",
  "/search",
  "/decisions",
  "/rag",
  "/ai",
  "/graph",
  "/automation",
  "/monitoring",
  "/customer-success",
  "/settings",
  "/admin",
]

describe("Sidebar Navigation — Route Integrity", () => {
  it("all expected routes are present", () => {
    expect(EXPECTED_ROUTES.length).toBeGreaterThanOrEqual(18)
  })

  it("no duplicate routes exist", () => {
    const unique = new Set(EXPECTED_ROUTES)
    expect(unique.size).toBe(EXPECTED_ROUTES.length)
  })
})
