import {
  createCustomField,
  getCustomFieldsFormSchema,
  listCustomFieldSchema,
  projectCustomFieldValues,
} from "../tenantStudio";

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

describe("tenantStudio API — FE-S10-01/02", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip custom-fields schema by object_key", async () => {
    mocked.get.mockResolvedValue({
      data: {
        tenant_id: "t1",
        object_key: "company",
        schema_version: 1,
        fields: [],
      },
    });
    const schema = await listCustomFieldSchema("tenant-1", "company");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/custom-fields/company",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
    expect(schema.object_key).toBe("company");
  });

  it("POSTs tip custom field definition", async () => {
    mocked.post.mockResolvedValue({
      data: {
        id: "f1",
        tenant_id: "t1",
        object_key: "contact",
        field_key: "nickname",
        field_type: "string",
        label: "Nickname",
        schema_version: 1,
        enum_values: [],
      },
    });
    const row = await createCustomField("tenant-1", {
      object_key: "contact",
      field_key: "nickname",
      field_type: "string",
      label: "Nickname",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/custom-fields",
      expect.objectContaining({
        object_key: "contact",
        field_key: "nickname",
      }),
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
    expect(row.field_key).toBe("nickname");
  });

  it("GETs tip form-schema for auto-render", async () => {
    mocked.get.mockResolvedValue({
      data: {
        id: "custom-fields:company:v0",
        title: "Custom fields (company)",
        fields: [],
        object_key: "company",
        tenant_id: "t1",
        schema_version: 0,
        values: {},
        bag_key: "custom_fields",
        renderer: "custom_fields_auto",
      },
    });
    const form = await getCustomFieldsFormSchema("tenant-1", "company");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/custom-fields/company/form-schema",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
    expect(form.renderer).toBe("custom_fields_auto");
  });

  it("POSTs tip values projection", async () => {
    mocked.post.mockResolvedValue({
      data: {
        object_key: "company",
        bag_key: "custom_fields",
        values: { segment_tier: "A" },
        metadata: { custom_fields: { segment_tier: "A" } },
      },
    });
    const row = await projectCustomFieldValues("tenant-1", "company", {
      values: { segment_tier: "A" },
      metadata: {},
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/custom-fields/company/values",
      expect.objectContaining({ values: { segment_tier: "A" } }),
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
    expect(row.metadata.custom_fields).toEqual({ segment_tier: "A" });
  });
});
