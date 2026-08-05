import { render, screen, fireEvent, waitFor } from "@testing-library/react";

beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});

jest.mock("@/lib/api", () => {
  const mockGet = jest.fn();
  return { __esModule: true, default: { get: mockGet }, get: mockGet };
});

jest.mock("@/lib/i18n", () => ({
  useTranslation: jest.fn().mockReturnValue({
    t: (s: string) => {
      const map: Record<string, string> = {
        "graph.title": "Knowledge Graph",
        "graph.search_placeholder": "Search entities...",
        "graph.company": "Company",
        "graph.contact": "Contact",
        "graph.employee": "Employee",
        "graph.opportunity": "Opportunity",
        "graph.total_nodes": "Nodes",
        "graph.total_edges": "Edges",
        "graph.empty_state": "Search for entities or load demo data",
        "graph.no_results": "No results found",
        "graph.loading_graph": "Loading graph...",
        "graph.node_details": "Node Details",
        "graph.relationships": "Relationships",
        "graph.no_relationships": "No relationships",
        "graph.expand": "Expand",
        "graph.zoom_in": "Zoom In",
        "graph.zoom_out": "Zoom Out",
        "graph.reset_view": "Reset View",
        "common.search": "Search",
      };
      return map[s] || s;
    },
    locale: "en",
  }),
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  useTenant: jest.fn().mockReturnValue({ tenantId: "tenant-1" }),
}));

import api from "@/lib/api";
import KnowledgeGraphPage from "../page";

const mockApiGet = (api as unknown as { get: jest.Mock }).get;

describe("KnowledgeGraphPage", () => {
  beforeEach(() => jest.clearAllMocks());

  it("renders without crashing", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByText("Knowledge Graph")).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByPlaceholderText("Search entities...")).toBeInTheDocument();
  });

  it("renders search button", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("shows legend with node types", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByText("Company")).toBeInTheDocument();
    expect(screen.getByText("Contact")).toBeInTheDocument();
    expect(screen.getByText("Employee")).toBeInTheDocument();
    expect(screen.getByText("Opportunity")).toBeInTheDocument();
  });

  it("shows empty state message before search", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByText("Search for entities or load demo data")).toBeInTheDocument();
  });

  it("shows demo button", () => {
    render(<KnowledgeGraphPage />);
    expect(screen.getByText("Expand")).toBeInTheDocument();
  });

  it("loads demo data when expand button is clicked", async () => {
    render(<KnowledgeGraphPage />);
    fireEvent.click(screen.getByText("Expand"));
    await waitFor(() => {
      expect(screen.getByText(/Nodes/)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/Edges/)).toBeInTheDocument();
    });
  });

  it("calls API on search", async () => {
    mockApiGet.mockResolvedValueOnce({ data: { results: [] } });
    render(<KnowledgeGraphPage />);
    const input = screen.getByPlaceholderText("Search entities...");
    fireEvent.change(input, { target: { value: "aramco" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        "/api/v1/graph/search",
        expect.objectContaining({ params: { q: "aramco", limit: 50 } })
      );
    });
  });

  it("falls back to demo data on API error", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    render(<KnowledgeGraphPage />);
    const input = screen.getByPlaceholderText("Search entities...");
    fireEvent.change(input, { target: { value: "test" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByText(/Nodes/)).toBeInTheDocument();
    });
  });

  it("shows zoom controls", () => {
    const { container } = render(<KnowledgeGraphPage />);
    const zoomIn = container.querySelector(".lucide-zoom-in");
    const zoomOut = container.querySelector(".lucide-zoom-out");
    const maximize = container.querySelector(".lucide-maximize2");
    expect(zoomIn).toBeInTheDocument();
    expect(zoomOut).toBeInTheDocument();
    expect(maximize).toBeInTheDocument();
  });

  it("disables search when query is empty", () => {
    render(<KnowledgeGraphPage />);
    const searchBtn = screen.getByRole("button", { name: /search/i });
    expect(searchBtn).toBeDisabled();
  });

  it("enables search when query is entered", () => {
    render(<KnowledgeGraphPage />);
    const input = screen.getByPlaceholderText("Search entities...");
    fireEvent.change(input, { target: { value: "hello" } });
    const searchBtn = screen.getByRole("button", { name: /search/i });
    expect(searchBtn).not.toBeDisabled();
  });

  it("loads demo data from API results", async () => {
    mockApiGet.mockResolvedValueOnce({
      data: {
        results: [
          { id: "c1", name: "Aramco", type: "company" },
          { id: "c2", name: "SABIC", type: "company" },
        ],
      },
    });
    render(<KnowledgeGraphPage />);
    const input = screen.getByPlaceholderText("Search entities...");
    fireEvent.change(input, { target: { value: "companies" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByText("(2)")).toBeInTheDocument();
    });
  });
});
