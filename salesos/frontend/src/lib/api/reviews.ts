import api from "./client";

/** 201 payload from POST /api/v1/reviews — not a full review record. */
export interface CreateReviewResponse {
  id: string;
  status: string;
  review_type: string;
}

/**
 * POST /api/v1/reviews — query `review_type` + `target_id` + `target_type` required.
 * `assigned_to` defaults to "" on the server. Null body.
 */
export async function createReview(
  tenantId: string,
  reviewType: string,
  targetId: string,
  targetType: string,
  assignedTo = ""
): Promise<CreateReviewResponse> {
  const response = await api.post("/api/v1/reviews", null, {
    params: {
      review_type: reviewType,
      target_id: targetId,
      target_type: targetType,
      assigned_to: assignedTo,
    },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
