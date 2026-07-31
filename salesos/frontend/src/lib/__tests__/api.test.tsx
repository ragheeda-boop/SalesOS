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
};
jest.mock("axios", () => mockAxios);

import api from "../api";

describe("api instance", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("creates axios instance", () => {
    expect(api).toBeDefined();
  });

  it("has request interceptor registered", () => {
    expect(api.interceptors.request.use).toHaveBeenCalled();
  });

  it("has response interceptor registered", () => {
    expect(api.interceptors.response.use).toHaveBeenCalled();
  });
});
