import { render, screen, fireEvent, waitFor } from '@testing-library/react'

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: { post: jest.fn() },
}))

jest.mock('@/lib/hooks/useTenant', () => ({
  getTenantId: jest.fn().mockReturnValue('tenant-1'),
}))

import api from '@/lib/api'
import { CopilotPanel } from '../copilot-panel'

const mockPost = api.post as jest.Mock

beforeAll(() => {
  HTMLElement.prototype.scrollIntoView = jest.fn()
  Element.prototype.scrollTo = jest.fn()
})

describe('CopilotPanel', () => {
  beforeEach(() => jest.clearAllMocks())

  it('renders nothing when closed', () => {
    const { container } = render(<CopilotPanel open={false} onClose={jest.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders panel when open', () => {
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    expect(screen.getByText('المساعد الذكي')).toBeInTheDocument()
    expect(screen.getByText('AI')).toBeInTheDocument()
  })

  it('shows default welcome message without entityType', () => {
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    expect(screen.getByText(/مرحباً! أنا المساعد الذكي/)).toBeInTheDocument()
  })

  it('shows company-specific welcome when entityType is company', () => {
    render(<CopilotPanel open={true} onClose={jest.fn()} entityType="company" />)
    expect(screen.getByText(/كيف يمكنني مساعدتك في تحليل هذه الشركة/)).toBeInTheDocument()
  })

  it('shows data-specific welcome for other entity types', () => {
    render(<CopilotPanel open={true} onClose={jest.fn()} entityType="deal" />)
    expect(screen.getByText(/كيف يمكنني مساعدتك في تحليل هذه البيانات/)).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn()
    render(<CopilotPanel open={true} onClose={onClose} />)
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[0])
    expect(onClose).toHaveBeenCalled()
  })

  it('sends message on Enter key', async () => {
    mockPost.mockResolvedValue({ data: { response: 'رد تجريبي' } })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال تجريبي' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => expect(mockPost).toHaveBeenCalled())
  })

  it('sends message on send button click', async () => {
    mockPost.mockResolvedValue({ data: { response: 'رد' } })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[buttons.length - 1])
    await waitFor(() => expect(mockPost).toHaveBeenCalled())
  })

  it('does not send empty messages', () => {
    mockPost.mockResolvedValue({ data: { response: 'رد' } })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(mockPost).not.toHaveBeenCalled()
  })

  it('displays user message after sending', async () => {
    mockPost.mockResolvedValue({ data: { response: 'رد تجريبي' } })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText('سؤال')).toBeInTheDocument()
    })
  })

  it('displays assistant response after API call', async () => {
    mockPost.mockResolvedValue({ data: { response: 'هذا رد من المساعد' } })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText('هذا رد من المساعد')).toBeInTheDocument()
    })
  })

  it('shows error message on API failure', async () => {
    mockPost.mockRejectedValue(new Error('Network error'))
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText(/عذراً، حدث خطأ/)).toBeInTheDocument()
    })
  })

  it('shows default response when API returns empty', async () => {
    mockPost.mockResolvedValue({ data: {} })
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(screen.getByText('لم يتم العثور على رد.')).toBeInTheDocument()
    })
  })

  it('passes context to API', async () => {
    mockPost.mockResolvedValue({ data: { response: 'رد' } })
    render(
      <CopilotPanel
        open={true}
        onClose={jest.fn()}
        entityType="company"
        entityId="c1"
        context={{ company_name: 'أرامكو', cr_number: '1234', city: 'الرياض' }}
      />
    )
    const input = screen.getByPlaceholderText('اسأل المساعد الذكي...')
    fireEvent.change(input, { target: { value: 'سؤال' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/copilot/query',
        expect.objectContaining({ company_id: 'c1', company_name: 'أرامكو', cr_number: '1234', city: 'الرياض' }),
        expect.any(Object)
      )
    })
  })

  it('disables send button when input is empty', () => {
    render(<CopilotPanel open={true} onClose={jest.fn()} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons[buttons.length - 1]).toBeDisabled()
  })
})
