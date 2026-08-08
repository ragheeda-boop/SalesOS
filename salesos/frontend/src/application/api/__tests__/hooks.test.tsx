/* eslint-disable @typescript-eslint/no-explicit-any */
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

jest.mock("@/lib/hooks/useTenant");
jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

import { getTenantId } from "@/lib/hooks/useTenant";
import api from "@/lib/api";
import {
  useOpportunities,
  useTasks,
  usePipeline,
  useCreateOpportunity,
  useCreateTask,
  useCompleteTask,
} from "../hooks";

const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>;
const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useOpportunities", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("fetches opportunities", async () => {
    mockedApi.get.mockResolvedValue({ data: [{ id: "o-1" }] } as any);

    const { result } = renderHook(() => useOpportunities(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: "o-1" }]);
  });

  it("filters by stage", async () => {
    mockedApi.get.mockResolvedValue({ data: [] } as any);

    renderHook(() => useOpportunities("won"), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/opportunities", {
        params: { stage: "won" },
        headers: { "X-Tenant-Id": "tenant-1" },
      });
    });
  });
});

describe("useTasks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("fetches tasks", async () => {
    mockedApi.get.mockResolvedValue({ data: [{ id: "t-1" }] } as any);

    const { result } = renderHook(() => useTasks(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: "t-1" }]);
  });
});

describe("usePipeline", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("fetches pipeline", async () => {
    mockedApi.get.mockResolvedValue({ data: { stages: [] } } as any);

    const { result } = renderHook(() => usePipeline(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ stages: [] });
  });
});

describe("useCreateOpportunity", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("creates opportunity via mutation", async () => {
    mockedApi.post.mockResolvedValue({ data: { id: "o-2" } } as any);

    const { result } = renderHook(() => useCreateOpportunity(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      companyId: "c-1",
      companyName: "Acme",
      name: "Deal",
      estimatedValue: 1000,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe("useCreateTask", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("creates task via mutation", async () => {
    mockedApi.post.mockResolvedValue({ data: { id: "t-2" } } as any);

    const { result } = renderHook(() => useCreateTask(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ title: "New Task" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe("useCompleteTask", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetTenantId.mockReturnValue("tenant-1");
  });

  it("completes task via mutation", async () => {
    mockedApi.put.mockResolvedValue({
      data: { id: "t-1", completed: true },
    } as any);

    const { result } = renderHook(() => useCompleteTask(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("t-1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.put).toHaveBeenCalledWith(
      "/api/v1/tasks/t-1/complete",
      null,
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      })
    );
  });
});
