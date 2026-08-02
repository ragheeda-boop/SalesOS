import {
  advanceEnrollment,
  createSequence,
  enrollContact,
  getSequencingMeta,
  listSequences,
} from "../sequences";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("sequences API — FE-S11-09", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "SequenceDefinition",
        channels: ["email", "linkedin", "whatsapp"],
        linkedin_policy: "compliant partner API only — no ToS-risk automation",
        binding: "Activity/Task",
        honesty: "CI in-memory; live network not claimed",
      },
    });
    const meta = await getSequencingMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/sequences/meta",
      expect.any(Object),
    );
    expect(meta.channels).toContain("email");
    mocked.get.mockResolvedValueOnce({ data: [] });
    await listSequences("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/sequences",
      expect.any(Object),
    );
  });

  it("POSTs create, enroll, advance", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "seq1",
        tenant_id: "tenant-1",
        name: "Pilot",
        steps: [
          {
            id: "s1",
            day_offset: 0,
            channel: "email",
            subject: "Hi",
            body: "Body",
          },
        ],
        channel: "email",
        schema_version: 1,
        step_count: 1,
      },
    });
    await createSequence("tenant-1", {
      name: "Pilot",
      steps: [{ subject: "Hi", body: "Body", day_offset: 0 }],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/sequences",
      expect.objectContaining({ name: "Pilot" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({
      data: {
        id: "enr1",
        tenant_id: "tenant-1",
        sequence_id: "seq1",
        contact_email: "a@b.com",
        status: "active",
        current_step_index: 0,
        step_states: [{ step_id: "s1", status: "pending", day_offset: 0 }],
        task_bindings: [],
        activity_bindings: [],
        schema_version: 1,
        bound_to_task_activity: true,
      },
    });
    await enrollContact("tenant-1", "seq1", { contact_email: "a@b.com" });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/sequences/seq1/enrollments",
      expect.objectContaining({ contact_email: "a@b.com" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({
      data: {
        id: "enr1",
        tenant_id: "tenant-1",
        sequence_id: "seq1",
        contact_email: "a@b.com",
        status: "completed",
        current_step_index: 1,
        step_states: [{ step_id: "s1", status: "sent", day_offset: 0 }],
        task_bindings: [
          {
            task_id: "t1",
            title: "Send",
            source: "sequence",
            completed: true,
            step_id: "s1",
          },
        ],
        activity_bindings: [],
        schema_version: 1,
        bound_to_task_activity: true,
      },
    });
    const advanced = await advanceEnrollment("tenant-1", "enr1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/sequences/enrollments/enr1/advance",
      {},
      expect.any(Object),
    );
    expect(advanced.task_bindings).toHaveLength(1);
  });
});
