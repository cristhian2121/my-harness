import type { AskResult, HealthStatus, HistoryItem, UserRecord } from "@/lib/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(payload?.detail ?? "Unexpected API error.", response.status);
  }

  return (await response.json()) as T;
}

export async function registerUser(input: {
  username: string;
  role: string;
}): Promise<UserRecord> {
  const payload = await request<{ user: UserRecord }>("/init_user", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return payload.user;
}

export async function validateUser(input: {
  username: string;
  role: string;
}): Promise<UserRecord> {
  const payload = await request<{ user: UserRecord }>("/validate_user", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return payload.user;
}

export function askQuestion(
  input: { username: string; message: string },
  signal?: AbortSignal,
): Promise<AskResult> {
  return request<AskResult>("/ask", {
    method: "POST",
    body: JSON.stringify(input),
    signal,
  });
}

export async function getHistory(username: string): Promise<HistoryItem[]> {
  const payload = await request<{ items: HistoryItem[] }>(`/history/${username}`);
  return payload.items;
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export { ApiError };
