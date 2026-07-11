"use client"

import { useEffect, useState } from "react"
import api from "@/lib/api"

interface Scenario {
  id: string
  title: string
  description: string
  steps: { order: number; action: string; label: string }[]
}

interface StepResult {
  step: number
  action: string
  label: string
  data: Record<string, any>
}

export function ScenarioLauncher() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [activeScenario, setActiveScenario] = useState<string | null>(null)
  const [results, setResults] = useState<StepResult[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get("/api/v1/demo/scenarios")
      .then((res) => setScenarios(res.data))
      .catch(() => {})
  }, [])

  const runScenario = async (scenarioId: string) => {
    setRunning(true)
    setActiveScenario(scenarioId)
    setResults([])
    setError(null)

    const scenario = scenarios.find((s) => s.id === scenarioId)
    if (!scenario) return

    const stepResults: StepResult[] = []

    for (const step of scenario.steps) {
      stepResults.push({
        step: step.order,
        action: step.action,
        label: step.label,
        data: { narrative: `Executed: ${step.label}`, status: "simulated" },
      })
    }

    setResults(stepResults)
    setRunning(false)
  }

  if (scenarios.length === 0) return null

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Demo Scenarios</h3>
      <p className="text-sm text-muted-foreground">
        Run pre-built walkthroughs to demonstrate SalesOS capabilities.
      </p>

      <div className="grid gap-3">
        {scenarios.map((scenario) => (
          <div
            key={scenario.id}
            className="border rounded-lg p-4 space-y-2 bg-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium">{scenario.title}</h4>
                <p className="text-sm text-muted-foreground">
                  {scenario.description}
                </p>
              </div>
              <button
                onClick={() => runScenario(scenario.id)}
                disabled={running}
                className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50"
              >
                {running && activeScenario === scenario.id
                  ? "Running..."
                  : "Run Scenario"}
              </button>
            </div>

            {scenario.steps && (
              <div className="flex gap-2 text-xs text-muted-foreground">
                {scenario.steps.map((step) => (
                  <span key={step.order} className="flex items-center gap-1">
                    <span className="w-5 h-5 rounded-full bg-muted flex items-center justify-center text-xs">
                      {step.order}
                    </span>
                    {step.label}
                  </span>
                ))}
              </div>
            )}

            {activeScenario === scenario.id && results.length > 0 && (
              <div className="mt-3 space-y-2 border-t pt-3">
                {results.map((result) => (
                  <div
                    key={result.step}
                    className="text-sm bg-muted/50 rounded p-2"
                  >
                    <span className="font-medium">
                      Step {result.step}: {result.label}
                    </span>
                    <p className="text-muted-foreground mt-1">
                      {result.data?.narrative ||
                        result.data?.status ||
                        "Completed"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
