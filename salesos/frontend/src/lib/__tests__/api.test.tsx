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
jest.mock('axios', () => mockAxios)

describe('api instance', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('creates axios instance', () => {
    const api = require('../api').default
    expect(api).toBeDefined()
  })

  it('has request interceptor registered', () => {
    const api = require('../api').default
    expect(api.interceptors.request.use).toHaveBeenCalled()
  })

  it('has response interceptor registered', () => {
    const api = require('../api').default
    expect(api.interceptors.response.use).toHaveBeenCalled()
  })
})
