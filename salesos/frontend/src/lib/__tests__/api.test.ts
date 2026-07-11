import api from '../api'

jest.mock('axios', () => {
  const mockAxios = {
    create: jest.fn(() => mockAxios),
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  }
  return { default: mockAxios }
})

describe('api instance', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('has interceptors registered', () => {
    const axios = require('axios').default
    expect(axios.interceptors.request.use).toHaveBeenCalledTimes(1)
    expect(axios.interceptors.response.use).toHaveBeenCalledTimes(1)
  })

  it('has baseURL configured', () => {
    const axios = require('axios').default
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: expect.any(String),
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })
})
