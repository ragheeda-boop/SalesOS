import api from "@/lib/api"

export async function getDashboard(tenantId: string): Promise<unknown> {
  const response = await api.get("/api/v1/dashboard", {
    headers: { "X-Tenant-Id": tenantId },
  })
  return response.data
}
