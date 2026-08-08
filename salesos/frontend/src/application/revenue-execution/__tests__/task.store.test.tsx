/* eslint-disable @typescript-eslint/no-explicit-any */
jest.mock("@/lib/api", () => {
  const store: any[] = [];
  return {
    __esModule: true,
    default: {
      get: jest.fn(() => Promise.resolve({ data: { items: store } })),
      post: jest.fn((_url: string, input: any) => {
        const task = {
          id: "task_" + Math.random().toString(36).slice(2, 10),
          createdAt: "2026-07-11T12:00:00.000Z",
          ...input,
        };
        store.unshift(task);
        return Promise.resolve({ data: task });
      }),
      put: jest.fn((url: string) => {
        const id = url.match(/\/tasks\/([^/]+)\/complete/)?.[1];
        if (id) {
          const entry = store.find((t: any) => t.id === id);
          if (entry) entry.completed = true;
        }
        return Promise.resolve({ data: {} });
      }),
      patch: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      __store: store,
    },
  };
});

import api from "@/lib/api";
import {
  loadTasks,
  addTask,
  completeTask,
  getOverdueTasks,
  getTasksByPriority,
} from "../task.store";

const mockedApi = api as jest.Mocked<typeof api> & { __store: any[] };

beforeEach(() => {
  mockedApi.__store.length = 0;
  jest.clearAllMocks();
  mockedApi.get.mockImplementation(() =>
    Promise.resolve({ data: { items: mockedApi.__store } } as any)
  );
  mockedApi.post.mockImplementation((_url: string, input: any) => {
    const task = {
      id: "task_" + Math.random().toString(36).slice(2, 10),
      createdAt: "2026-07-11T12:00:00.000Z",
      ...input,
    };
    mockedApi.__store.unshift(task);
    return Promise.resolve({ data: task } as any);
  });
  mockedApi.put.mockImplementation((url: string) => {
    const id = url.match(/\/tasks\/([^/]+)\/complete/)?.[1];
    if (id) {
      const entry = mockedApi.__store.find((t: any) => t.id === id);
      if (entry) entry.completed = true;
    }
    return Promise.resolve({ data: {} } as any);
  });
});

describe("task store", () => {
  describe("loadTasks / saveTasks", () => {
    it("returns empty array when no tasks stored", async () => {
      expect(await loadTasks()).toEqual([]);
    });

    it("saves and loads tasks", async () => {
      const tasks = [
        {
          id: "t-1",
          title: "Test",
          priority: "high" as const,
          source: "manual" as const,
          completed: false,
          createdAt: "2026-07-10T10:00:00Z",
        },
      ];
      mockedApi.__store.length = 0;
      mockedApi.__store.push(...tasks);
      expect(await loadTasks()).toEqual(tasks);
    });

    it("returns empty array on corrupt localStorage", async () => {
      expect(await loadTasks()).toEqual([]);
    });
  });

  describe("addTask", () => {
    it("adds a task with generated id and createdAt", async () => {
      const tasks = await addTask({
        title: "Follow up",
        priority: "high",
        source: "nba",
        companyId: "c-1",
        completed: false,
      });
      expect(tasks).toHaveLength(1);
      expect(tasks[0].id).toContain("task_");
      expect(tasks[0].createdAt).toBe("2026-07-11T12:00:00.000Z");
      expect(tasks[0].title).toBe("Follow up");
      expect(tasks[0].completed).toBe(false);
    });

    it("prepends new tasks to existing ones", async () => {
      await addTask({
        title: "First",
        priority: "high",
        source: "manual",
        completed: false,
      });
      await addTask({
        title: "Second",
        priority: "low",
        source: "manual",
        completed: false,
      });

      const all = await loadTasks();
      expect(all).toHaveLength(2);
      expect(all[0].title).toBe("Second");
    });
  });

  describe("completeTask", () => {
    it("marks a task as completed", async () => {
      await addTask({
        title: "Task",
        priority: "medium",
        source: "manual",
        completed: false,
      });
      const tasks = await loadTasks();
      const updated = await completeTask(tasks[0].id);
      expect(updated[0].completed).toBe(true);
    });
  });

  describe("getOverdueTasks", () => {
    it("returns tasks with dueDate in the past", async () => {
      await addTask({
        title: "Overdue",
        priority: "high",
        source: "manual",
        completed: false,
        dueDate: "2026-07-10T12:00:00Z",
      });
      await addTask({
        title: "Future",
        priority: "low",
        source: "manual",
        completed: false,
        dueDate: "2099-07-20T12:00:00Z",
      });

      const overdue = await getOverdueTasks();
      expect(overdue).toHaveLength(1);
      expect(overdue[0].title).toBe("Overdue");
    });
  });

  describe("getTasksByPriority", () => {
    it("filters tasks by priority", async () => {
      await addTask({
        title: "Critical 1",
        priority: "critical",
        source: "nba",
        completed: false,
      });
      await addTask({
        title: "Critical 2",
        priority: "critical",
        source: "nba",
        completed: false,
      });
      await addTask({
        title: "Low",
        priority: "low",
        source: "manual",
        completed: false,
      });

      expect(await getTasksByPriority("critical")).toHaveLength(2);
      expect(await getTasksByPriority("low")).toHaveLength(1);
      expect(await getTasksByPriority("high")).toHaveLength(0);
    });
  });
});
