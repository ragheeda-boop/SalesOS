'use client'

import { KPIView } from './KPIView'
import type { EmployeeKPIs } from '@/lib/api'

export function KPIContainer({ data }: { data: EmployeeKPIs }) {
  return <KPIView data={data} />
}
