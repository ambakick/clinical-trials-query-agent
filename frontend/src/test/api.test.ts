import { beforeEach, describe, expect, it, vi } from "vitest";
import { submitQuery } from "../lib/api";
import { loadRealOutput } from "./fixtures";

describe("submitQuery", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("parses a query response", async () => {
    const payload = loadRealOutput("1a. Time Trend — Pembrolizumab since 2015");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const response = await submitQuery({ query: "How has pembrolizumab changed since 2015?", citation_mode: "deep", max_results: 3000 });
    expect("visualization" in response).toBe(true);
    if ("visualization" in response) {
      expect(response.visualization.type).toBe("time_series");
    }
  });

  it("parses a clarification response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "needs_clarification",
          reason: "Comparison target is ambiguous",
          question: "Which two drugs should be compared?",
        }),
      }),
    );

    const response = await submitQuery({ query: "Compare immunotherapy drugs", citation_mode: "deep", max_results: 3000 });
    expect("status" in response && response.status === "needs_clarification").toBe(true);
  });
});
