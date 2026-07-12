function createMockFn() {
  const fn = function() { return fn }
  fn.mockReturnThis = function() { return this; return fn }
  return fn
}

const server = {
  listen: createMockFn(),
  close: createMockFn(),
  resetHandlers: createMockFn(),
  use: createMockFn(),
  events: {
    on: createMockFn(),
    removeAllListeners: createMockFn(),
  },
  listHandlers: createMockFn(() => []),
  printHandlers: createMockFn(),
}

function setupServer(...args) {
  return server
}

module.exports = { setupServer, server }
