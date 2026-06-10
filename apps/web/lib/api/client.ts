import { isFastApiErrorBody } from "@/lib/api/safe";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function requestJson<T>(
  path: string,
  init?: RequestInit
): Promise<{ payload: T | null; consolePayload: string; status: number | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      }
    });
    const contentType = response.headers.get("content-type") ?? "";
    if (!contentType.includes("application/json")) {
      const bytes = await response.arrayBuffer();
      const payload = {
        status: response.status,
        content_type: contentType,
        bytes: bytes.byteLength
      };
      return {
        payload: null,
        consolePayload: JSON.stringify(payload, null, 2),
        status: response.status
      };
    }
    const payload = (await response.json()) as T;
    if (!response.ok || isFastApiErrorBody(payload)) {
      return {
        payload: null,
        consolePayload: JSON.stringify(
          { status: response.status, error: payload },
          null,
          2
        ),
        status: response.status
      };
    }
    return {
      payload,
      consolePayload: JSON.stringify(payload, null, 2),
      status: response.status
    };
  } catch (error) {
    return {
      payload: null,
      consolePayload: error instanceof Error ? error.message : "Unknown API error",
      status: null
    };
  }
}
