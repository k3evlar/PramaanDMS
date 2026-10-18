import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { fetchServiceStatus } from "./api";

function fakeFetch(status: number, body: unknown): typeof fetch {
  return (async () => new Response(JSON.stringify(body), { status })) as typeof fetch;
}

afterEach(cleanup);

describe("App", () => {
  it("shows the product name", () => {
    render(<App fetchImpl={fakeFetch(200, { status: "ok" })} />);
    expect(screen.getByRole("heading", { name: "Pramaan DMS" })).toBeTruthy();
  });

  it("says the service is running when the API is healthy", async () => {
    render(<App fetchImpl={fakeFetch(200, { status: "ok" })} />);
    expect(await screen.findByText("The service is running.")).toBeTruthy();
  });

  it("says the service is not reachable when the API fails", async () => {
    render(<App fetchImpl={fakeFetch(503, { status: "degraded" })} />);
    expect(await screen.findByText(/not reachable/)).toBeTruthy();
  });
});

describe("fetchServiceStatus", () => {
  it("treats a network error as unavailable", async () => {
    const failing = (async () => {
      throw new TypeError("network down");
    }) as typeof fetch;
    expect(await fetchServiceStatus(failing)).toBe("unavailable");
  });

  it("treats an unexpected body as unavailable", async () => {
    expect(await fetchServiceStatus(fakeFetch(200, { status: "maybe" }))).toBe("unavailable");
  });
});
