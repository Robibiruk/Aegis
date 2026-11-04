export type Task = {
  id: string;
  title: string;
  notes: string | null;
  due_at: string | null;
  timezone: string;
  status: "open" | "completed" | "cancelled";
};

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Request failed");
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
