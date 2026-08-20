import { render, screen, waitFor, fireEvent } from "@testing-library/react";

jest.mock("next/link", () => {
  function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  }
  MockLink.displayName = "MockLink";
  return MockLink;
});

jest.mock("@/lib/hooks/useTenant", () => ({
  useTenant: () => ({ tenantId: "tenant-1" }),
}));

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

import api from "@/lib/api";
import TasksPage from "../page";

const mockGet = (api as unknown as { get: jest.Mock }).get;
const mockPut = (api as unknown as { put: jest.Mock }).put;

const sampleTasks = [
  {
    id: "t-1",
    title: "متابعة العميل",
    priority: "high",
    source: "nba",
    company_id: "c-1",
    completed: false,
    created_at: "2026-07-10T10:00:00Z",
  },
  {
    id: "t-2",
    title: "إرسال العرض",
    priority: "low",
    completed: true,
    created_at: "2026-07-09T10:00:00Z",
  },
];

describe("TasksPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows empty state when the API returns no tasks", async () => {
    mockGet.mockResolvedValue({ data: [] });
    render(<TasksPage />);
    expect(await screen.findByText("لا توجد مهام")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /مهمة جديدة/ })).toHaveAttribute("href", "/tasks/new");
  });

  it("renders pending tasks and completes one", async () => {
    mockGet.mockResolvedValue({ data: sampleTasks });
    mockPut.mockResolvedValue({ data: { ...sampleTasks[0], completed: true } });
    render(<TasksPage />);

    expect(await screen.findByText("متابعة العميل")).toBeInTheDocument();
    expect(screen.queryByText("إرسال العرض")).not.toBeInTheDocument();

    const completeBtn = screen.getAllByRole("button").find((btn) =>
      btn.className.includes("rounded border-2")
    );
    expect(completeBtn).toBeDefined();
    fireEvent.click(completeBtn as HTMLElement);

    await waitFor(() => {
      expect(mockPut).toHaveBeenCalledWith(
        "/api/v1/tasks/t-1/complete",
        {},
        expect.objectContaining({
          headers: { "X-Tenant-Id": "tenant-1" },
        })
      );
    });
  });

  it("filters to completed tasks", async () => {
    mockGet.mockResolvedValue({ data: sampleTasks });
    render(<TasksPage />);
    expect(await screen.findByText("متابعة العميل")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "المكتملة" }));
    expect(screen.getByText("إرسال العرض")).toBeInTheDocument();
    expect(screen.queryByText("متابعة العميل")).not.toBeInTheDocument();
  });
});
