import type { GoldenRecordEntry, CompanyDNA } from '@/application/company-intelligence/company-intelligence.dto'
export interface GoldenRecordViewProps { entries: GoldenRecordEntry[]; dna?: CompanyDNA | null }
