import { render, screen } from '@testing-library/react'
import { AIBriefView } from '../AIBriefView'
import { AIBriefWidget } from '../AIBriefContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { AIBriefViewProps } from '../types'
import type { AIBriefData } from '@/application/dashboard/dashboard.dto'

const sampleData: AIBriefData = {
  summary: 'تم تحديد 3 فرص استراتيجية جديدة هذا الأسبوع في قطاع التقنية المالية',
  highlights: [
    'شركة ACME Corp تعلن عن شراكة استراتيجية مع بنك الرياض',
    'ارتفاع مؤشر الثقة بنسبة 15% في قطاع الطاقة',
    'فرصة توسع في السوق المصرية لشركة Beta Ltd',
  ],
  generatedAt: '2026-07-10T06:00:00.000Z',
}

const defaultProps: AIBriefViewProps = {
  summary: sampleData.summary,
  highlights: sampleData.highlights,
  generatedAt: sampleData.generatedAt,
}

function renderView(overrides?: Partial<AIBriefViewProps>) {
  return render(<AIBriefView {...defaultProps} {...overrides} />)
}

// ─── Contract Tests ───────────────────────────────────────────

describeWidgetContract({
  name: 'AIBrief',
  defaultData: sampleData,
  config: {
    metadata: {
      id: 'ai-brief',
      title: 'الملخص اليومي',
      minHeight: '200px',
      permissions: ['ai:read'],
      featureFlag: { enabled: true, tier: 'enabled' },
    },
    render: ({ data }) => (
      <AIBriefView
        summary={data.summary ?? ''}
        highlights={data.highlights ?? []}
        generatedAt={data.generatedAt}
      />
    ),
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

describe('AIBriefView', () => {
  it('renders summary text', () => {
    renderView()
    expect(screen.getByText(sampleData.summary)).toBeInTheDocument()
  })

  it('renders all highlights', () => {
    renderView()
    for (const h of sampleData.highlights) {
      expect(screen.getByText(h)).toBeInTheDocument()
    }
  })

  it('renders formatted timestamp', () => {
    renderView()
    expect(screen.getByText(/آخر تحديث/)).toBeInTheDocument()
  })

  it('shows empty state placeholder when no data', () => {
    renderView({ summary: '', highlights: [] })
    expect(screen.getByText('الملخص قيد الإعداد')).toBeInTheDocument()
    expect(screen.getByText(/سيظهر الملخص اليومي/)).toBeInTheDocument()
  })

  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'الملخص اليومي' })).toBeInTheDocument()
  })

  it('highlights have role="list" and role="listitem"', () => {
    renderView()
    expect(screen.getByRole('list')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(sampleData.highlights.length)
  })

  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })

  it('has motion-reduce class', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

// ─── SDK Integration ──────────────────────────────────────────

describe('AIBriefWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(AIBriefWidget).toBeDefined()
    expect(typeof AIBriefWidget === 'function' || typeof AIBriefWidget === 'object').toBe(true)
  })
})
