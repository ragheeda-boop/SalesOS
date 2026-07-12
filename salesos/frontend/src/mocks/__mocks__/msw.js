function fn() {
  const m = function () { return m }
  m.mockReturnThis = () => m
  m.mockReturnValue = () => m
  m.mockImplementation = () => m
  m.mockResolvedValue = () => m
  m.mockRejectedValue = () => m
  return m
}

const HttpResponse = {
  json: (body, init) => ({ body, init, _type: 'json' }),
  text: (body, init) => ({ body, init, _type: 'text' }),
}

const http = {
  all: fn(),
  get: fn(),
  post: fn(),
  put: fn(),
  patch: fn(),
  delete: fn(),
}

const graphql = { query: fn(), mutation: fn() }

module.exports = { http, HttpResponse, graphql }
