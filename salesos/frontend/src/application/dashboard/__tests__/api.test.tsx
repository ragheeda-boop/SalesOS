jest.mock('@/lib/api')

import api from '@/lib/api'
import { getDashboard } from '../api'

const mockedApi = api as jest.Mocked<typeof api>

describe('getDashboard', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('calls the dashboard API with tenant header', async () => {
    mockedApi.get.mockResolvedValue({ data: { totalTracked: 42 } })

    const result = await getDashboard('tenant-1')

    expect(result).toEqual({ totalTracked: 42 })
    expect(mockedApi.get).toHaveBeenCalledWith('/api/v1/dashboard', {
      headers: { 'X-Tenant-Id': 'tenant-1' },
    })
  })
})
