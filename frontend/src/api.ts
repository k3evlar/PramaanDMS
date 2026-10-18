// Minimal API client. All calls go to the same origin under /api (nginx proxies them),
// so no third-party hosts are contacted (ASVS V14.2.3).

export type ServiceStatus = "checking" | "available" | "unavailable";

export async function fetchServiceStatus(fetchImpl: typeof fetch = fetch): Promise<ServiceStatus> {
  try {
    const res = await fetchImpl("/api/health/live", { headers: { Accept: "application/json" } });
    if (!res.ok) {
      return "unavailable";
    }
    const body: unknown = await res.json();
    const ok = typeof body === "object" && body !== null && (body as { status?: unknown }).status === "ok";
    return ok ? "available" : "unavailable";
  } catch {
    return "unavailable";
  }
}
