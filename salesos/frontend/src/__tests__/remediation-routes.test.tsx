
describe("Remediation Route Pages — Module Resolution Smoke Tests", () => {
  const pages = [
    { name: "Revenue", importPath: "@/app/(dashboard)/revenue/page" },
    { name: "Pipeline", importPath: "@/app/(dashboard)/pipeline/page" },
    { name: "Forecast", importPath: "@/app/(dashboard)/forecast/page" },
    { name: "Decisions", importPath: "@/app/(dashboard)/decisions/page" },
    { name: "AI Registry", importPath: "@/app/(dashboard)/ai/page" },
    { name: "Knowledge Graph", importPath: "@/app/(dashboard)/graph/page" },
    { name: "Opportunity Detail", importPath: "@/app/(dashboard)/opportunities/[id]/page" },
  ]

  pages.forEach(({ name, importPath }) => {
    it(`${name} page module resolves without crashing`, async () => {
      const mod = await import(importPath)
      expect(mod.default).toBeDefined()
    })
  })
})
