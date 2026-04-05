import {
  type ApiResponse,
  type HealthResponse,
  type QueryRequest,
  ClarificationResponseSchema,
  HealthResponseSchema,
  QueryResponseSchema,
} from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    return JSON.stringify(payload);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export async function submitQuery(request: QueryRequest): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  const payload = await response.json();
  if (payload?.status === "needs_clarification") {
    return ClarificationResponseSchema.parse(payload);
  }
  return QueryResponseSchema.parse(payload);
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return HealthResponseSchema.parse(await response.json());
}
