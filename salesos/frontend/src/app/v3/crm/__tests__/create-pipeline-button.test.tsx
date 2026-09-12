import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

jest.mock("@/lib/api", () => ({
  createPipeline: jest.fn(),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

import { createPipeline } from "@/lib/api";
import { CreatePipelineButton } from "../create-pipeline-button";

const mockedCreate = createPipeline as jest.MockedFunction<typeof createPipeline>;

function renderButton() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <CreatePipelineButton />
    </QueryClientProvider>
  );
}

describe("CreatePipelineButton", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts createPipeline with no name/stages body and stays on CRM", async () => {
    mockedCreate.mockResolvedValueOnce({
      id: "pipe-tenant-1",
      name: "Sales Pipeline",
      stages: ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"],
    });
    renderButton();
    expect(screen.queryByTestId("create-pipeline-name")).toBeNull();
    expect(screen.queryByLabelText(/stages/i)).toBeNull();
    fireEvent.click(screen.getByTestId("create-pipeline-submit"));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith("tenant-1");
    });
    expect(mockedCreate).toHaveBeenCalledTimes(1);
    expect(await screen.findByTestId("create-pipeline-result")).toHaveTextContent(
      "Created Sales Pipeline (pipe-tenant-1"
    );
    expect(document.querySelector('a[href="/pipeline"]')).toBeNull();
    expect(document.querySelector('input[name="name"]')).toBeNull();
  });

  it("shows an honest 403 and does not invent a pipeline", async () => {
    mockedCreate.mockRejectedValueOnce({
      response: { status: 403, data: { detail: "forbidden" } },
    });
    renderButton();
    fireEvent.click(screen.getByTestId("create-pipeline-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You don't have permission to create pipelines."
    );
    expect(screen.queryByTestId("create-pipeline-result")).toBeNull();
  });
});
