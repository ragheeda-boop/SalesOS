import { getVerificationMeta, listVerificationRuns, runVerification } from "../verification";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
};

describe("verification API — FE-S11-06", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        channels: ["email", "phone"],
        statuses: ["valid", "invalid", "unknown", "risky"],
        connectors_configured: ["fake_verify"],
        interface: "VerificationConnector",
        honesty: "CI uses fake_verify",
      },
    });
    const meta = await getVerificationMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/verification/meta", expect.any(Object));
    expect(meta.connectors_configured).toEqual(["fake_verify"]);

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listVerificationRuns("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/verification", expect.any(Object));
  });

  it("POSTs run verification", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "ver1",
        tenant_id: "tenant-1",
        request: { email: "a@b.com", phone: "", provider_key: "" },
        verdicts: [
          {
            channel: "email",
            value: "a@b.com",
            status: "valid",
            confidence: 0.9,
            reason: "ok",
          },
        ],
        provider_key: "fake_verify",
        overall_status: "valid",
        schema_version: 1,
      },
    });
    const row = await runVerification("tenant-1", { email: "a@b.com" });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/verification",
      expect.objectContaining({ email: "a@b.com" }),
      expect.any(Object)
    );
    expect(row.overall_status).toBe("valid");
  });
});
