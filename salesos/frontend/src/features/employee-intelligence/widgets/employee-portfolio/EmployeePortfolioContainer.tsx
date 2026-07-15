'use client'

import { EmployeePortfolioView } from './EmployeePortfolioView'
import type { EmployeePortfolio } from '@/lib/api'

export function EmployeePortfolioContainer({ portfolio }: { portfolio: EmployeePortfolio }) {
  return <EmployeePortfolioView portfolio={portfolio} />
}
