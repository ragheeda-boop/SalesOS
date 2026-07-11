"use client"

import { useEffect, useState } from "react"
import api from "@/lib/api"

export function DemoBadge() {
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api
      .get("/api/v1/demo/status")
      .then((res) => setIsDemo(res.data?.demo_mode === true))
      .catch(() => setIsDemo(false))
  }, [])

  if (!isDemo) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[9999] bg-amber-500 text-black text-center text-xs font-bold py-1 tracking-wider">
      ⚡ DEMO MODE — All data is for demonstration purposes only
    </div>
  )
}
