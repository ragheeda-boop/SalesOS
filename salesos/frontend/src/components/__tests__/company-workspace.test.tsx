import { render, screen, fireEvent } from '@testing-library/react'

jest.mock('@/lib/hooks/companyQueries', () => ({
  useCompany: jest.fn(),
}))

jest.mock('@/lib/hooks/company360Queries', () => ({
  useCompany360: jest.fn(),
}))

jest.mock('@salesos/hooks', () => ({
  useLocalization: jest.fn().mockReturnValue({ t: (s: string) => s, locale: 'ar' }),
  useRuntime: jest.fn().mockReturnValue({}),
}))

jest.mock('@salesos/workspace', () => ({
  WorkspaceRenderer: (props: Record<string, unknown>) => (
    <div data-testid="workspace-renderer" data-loading={String(props.loading)} data-error={String(props.error)}>
      Workspace
    </div>
  ),
  generateWorkspace: jest.fn().mockReturnValue({ widgets: [], tabs: [] }),
}))

jest.mock('@salesos/design-language', () => ({
  AI_ACTIONS: {
    explain: { labelAr: 'شرح', labelEn: 'Explain' },
    analyze: { labelAr: 'تحليل', labelEn: 'Analyze' },
    predict: { labelAr: 'تنبؤ', labelEn: 'Predict' },
    summarize: { labelAr: 'تلخيص', labelEn: 'Summarize' },
    recommend: { labelAr: 'توصية', labelEn: 'Recommend' },
  },
}))

import { useCompany } from '@/lib/hooks/companyQueries'
import { useCompany360 } from '@/lib/hooks/company360Queries'
import { CompanyWorkspace } from '../company-workspace'

const mockUseCompany = useCompany as jest.Mock
const mockUseCompany360 = useCompany360 as jest.Mock

function makeCompany(overrides: Record<string, unknown> = {}) {
  return {
    name_ar: 'شركة أرامكو',
    name_en: 'Saudi Aramco',
    cr_number: '1234567890',
    city: 'الرياض',
    status: 'active',
    region: 'المنطقة الوسطى',
    ...overrides,
  }
}

describe('CompanyWorkspace', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading state', () => {
    mockUseCompany.mockReturnValue({ data: undefined, isLoading: true, isError: false })
    mockUseCompany360.mockReturnValue({ data: undefined })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByTestId('workspace-renderer')).toHaveAttribute('data-loading', 'true')
  })

  it('shows error state', () => {
    mockUseCompany.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    mockUseCompany360.mockReturnValue({ data: undefined })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByTestId('workspace-renderer')).toHaveAttribute('data-error', 'فشل تحميل بيانات الشركة')
  })

  it('renders company name', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('شركة أرامكو')).toBeInTheDocument()
  })

  it('renders English name when different from Arabic', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('Saudi Aramco')).toBeInTheDocument()
  })

  it('hides English name when same as Arabic', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany({ name_en: 'شركة أرامكو' }), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.queryByText('شركة أرامكو')).toBeInTheDocument()
  })

  it('renders CR number', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('1234567890')).toBeInTheDocument()
  })

  it('renders city', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('الرياض')).toBeInTheDocument()
  })

  it('shows dash when city is missing', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany({ city: '' }), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('-')).toBeInTheDocument()
  })

  it('renders status badge', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('renders preset buttons', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('مبيعات')).toBeInTheDocument()
    expect(screen.getByText('تسويق')).toBeInTheDocument()
    expect(screen.getByText('تنفيذي')).toBeInTheDocument()
    expect(screen.getByText('قانوني')).toBeInTheDocument()
    expect(screen.getByText('عمليات')).toBeInTheDocument()
    expect(screen.getByText('نجاح العملاء')).toBeInTheDocument()
  })

  it('switches preset on click', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    fireEvent.click(screen.getByText('تسويق'))
    expect(screen.getByTestId('workspace-renderer')).toBeInTheDocument()
  })

  it('renders AI action buttons', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('شرح')).toBeInTheDocument()
    expect(screen.getByText('تحليل')).toBeInTheDocument()
    expect(screen.getByText('تنبؤ')).toBeInTheDocument()
    expect(screen.getByText('تلخيص')).toBeInTheDocument()
    expect(screen.getByText('توصية')).toBeInTheDocument()
  })

  it('shows loading text when company is not loaded', () => {
    mockUseCompany.mockReturnValue({ data: undefined, isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: undefined })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByTestId('workspace-renderer')).toHaveAttribute('data-loading', 'false')
    expect(screen.getByTestId('workspace-renderer')).toHaveAttribute('data-error', 'undefined')
  })

  it('defaults to sales preset', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    const activeBtn = screen.getByText('مبيعات')
    expect(activeBtn.className).toContain('bg-[var(--muhide-orange)]')
  })
})
