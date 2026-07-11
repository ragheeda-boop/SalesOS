import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import type { NBARecommendation } from '../useNBA'

jest.mock('../useNBA')
import { useNBA } from '../useNBA'
import { NBAWidget } from '../NBAWidget'

const mockUseNBA = useNBA as jest.MockedFunction<typeof useNBA>
const mockGetNBA = jest.fn()
const mockRefreshNBA = jest.fn()
const mockAcceptNBA = jest.fn()
const mockDismissNBA = jest.fn()

jest.mock('../RecommendationCard', () => ({
  RecommendationCard: ({ recommendation, onAccept, onDismiss, onRefresh }: any) => (
    <div data-testid="recommendation-card">
      <span>{recommendation.action}</span>
      <span>{recommendation.reason}</span>
      <button onClick={onAccept}>تنفيذ</button>
      <button onClick={onDismiss}>تجاهل</button>
      <button onClick={onRefresh}>تحديث</button>
    </div>
  ),
}))

const sample: NBARecommendation = {
  id: 'nba-1',
  opportunityId: 'opp-1',
  action: 'meeting',
  reason: 'ارتفاع نية الشراء',
  confidence: 0.85,
  confidenceLabel: 'high',
  source: 'ai',
  alternatives: [{ action: 'send_proposal', reason: 'إرسال عرض', confidence: 0.7 }],
  evidence: [{ type: 'signal', description: 'إشارة شرائية قوية', source: 'LinkedIn', confidence: 0.9 }],
  potentialRisks: [{ type: 'competitor', level: 'medium', description: 'مورد بديل قيد التقييم' }],
  status: 'pending',
  createdAt: '2026-07-10T10:00:00Z',
  updatedAt: '2026-07-10T10:00:00Z',
}

function renderWidget(opportunityId = 'opp-1') {
  return render(<NBAWidget opportunityId={opportunityId} />)
}

describe('NBAWidget', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseNBA.mockReturnValue({
      getNBA: mockGetNBA,
      refreshNBA: mockRefreshNBA,
      acceptNBA: mockAcceptNBA,
      dismissNBA: mockDismissNBA,
    })
  })

  describe('1. Loading State', () => {
    it('renders loading skeleton on mount', () => {
      mockGetNBA.mockReturnValue(new Promise(() => {}))
      renderWidget()
      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.getByLabelText('Loading recommendation')).toBeInTheDocument()
    })

    it('shows animated pulse elements while loading', () => {
      mockGetNBA.mockReturnValue(new Promise(() => {}))
      renderWidget()
      const skeleton = screen.getByRole('status')
      expect(skeleton.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('2. Loaded State', () => {
    it('renders recommendation card when data arrives', async () => {
      mockGetNBA.mockResolvedValue(sample)
      renderWidget()
      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })
    })

    it('hides loading skeleton after data loads', async () => {
      mockGetNBA.mockResolvedValue(sample)
      renderWidget()
      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument()
      })
    })

    it('passes correct recommendation data to card', async () => {
      mockGetNBA.mockResolvedValue(sample)
      renderWidget()
      await waitFor(() => {
        expect(screen.getByText('meeting')).toBeInTheDocument()
        expect(screen.getByText('ارتفاع نية الشراء')).toBeInTheDocument()
      })
    })
  })

  describe('3. Error State', () => {
    it('renders error message when getNBA throws', async () => {
      mockGetNBA.mockRejectedValue(new Error('Network error'))
      renderWidget()
      await waitFor(() => {
        expect(screen.getByText('تعذر تحميل التوصية')).toBeInTheDocument()
      })
    })

    it('renders retry button on error', async () => {
      mockGetNBA.mockRejectedValue(new Error('Network error'))
      renderWidget()
      await waitFor(() => {
        expect(screen.getByText('حاول مرة أخرى')).toBeInTheDocument()
      })
    })

    it('retries loading when retry button clicked', async () => {
      mockGetNBA
        .mockRejectedValueOnce(new Error('fail'))
        .mockResolvedValueOnce(sample)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByText('حاول مرة أخرى')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('حاول مرة أخرى'))

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })
      expect(mockGetNBA).toHaveBeenCalledTimes(2)
    })
  })

  describe('4. No Recommendations', () => {
    it('renders empty state when getNBA returns null', async () => {
      mockGetNBA.mockResolvedValue(null)
      renderWidget()
      await waitFor(() => {
        expect(screen.getByText('لا توجد توصيات متاحة حاليًا')).toBeInTheDocument()
      })
    })

    it('renders refresh button in empty state', async () => {
      mockGetNBA.mockResolvedValue(null)
      renderWidget()
      await waitFor(() => {
        expect(screen.getByText('تحديث')).toBeInTheDocument()
      })
    })
  })

  describe('5. Accept', () => {
    it('calls acceptNBA with recommendation id', async () => {
      mockGetNBA.mockResolvedValue(sample)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تنفيذ'))

      await waitFor(() => {
        expect(mockAcceptNBA).toHaveBeenCalledWith('nba-1')
      })
    })

    it('does not call acceptNBA when no recommendation', async () => {
      mockGetNBA.mockResolvedValue(null)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByText('لا توجد توصيات متاحة حاليًا')).toBeInTheDocument()
      })

      expect(mockAcceptNBA).not.toHaveBeenCalled()
    })
  })

  describe('6. Dismiss', () => {
    it('calls dismissNBA with recommendation id', async () => {
      mockGetNBA.mockResolvedValue(sample)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تجاهل'))

      await waitFor(() => {
        expect(mockDismissNBA).toHaveBeenCalledWith('nba-1')
      })
    })

    it('shows empty state after dismiss', async () => {
      mockGetNBA.mockResolvedValue(sample)
      mockDismissNBA.mockResolvedValue(undefined)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تجاهل'))

      await waitFor(() => {
        expect(screen.getByText('لا توجد توصيات متاحة حاليًا')).toBeInTheDocument()
      })
    })
  })

  describe('7. Refresh', () => {
    it('calls refreshNBA on refresh button click', async () => {
      mockGetNBA.mockResolvedValue(sample)
      mockRefreshNBA.mockResolvedValue({ ...sample, id: 'nba-2' })
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تحديث'))

      await waitFor(() => {
        expect(mockRefreshNBA).toHaveBeenCalledTimes(1)
      })
    })

    it('updates recommendation after refresh', async () => {
      mockGetNBA.mockResolvedValue(sample)
      const refreshed = { ...sample, id: 'nba-2', reason: 'تحديث جديد' }
      mockRefreshNBA.mockResolvedValue(refreshed)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تحديث'))

      await waitFor(() => {
        expect(screen.getByText('تحديث جديد')).toBeInTheDocument()
      })
    })

    it('shows empty state when refresh returns null', async () => {
      mockGetNBA.mockResolvedValue(sample)
      mockRefreshNBA.mockResolvedValue(null)
      renderWidget()

      await waitFor(() => {
        expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('تحديث'))

      await waitFor(() => {
        expect(screen.getByText('لا توجد توصيات متاحة حاليًا')).toBeInTheDocument()
      })
    })
  })

  describe('8. Re-fetch on opportunityId change', () => {
    it('reloads when opportunityId prop changes', async () => {
      mockGetNBA.mockResolvedValue(sample)
      const { rerender } = render(<NBAWidget opportunityId="opp-1" />)

      await waitFor(() => {
        expect(mockGetNBA).toHaveBeenCalledTimes(1)
      })

      rerender(<NBAWidget opportunityId="opp-2" />)

      await waitFor(() => {
        expect(mockGetNBA).toHaveBeenCalledTimes(2)
      })
    })
  })
})
