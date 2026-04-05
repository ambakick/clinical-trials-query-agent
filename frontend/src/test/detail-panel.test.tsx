import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DetailPanel } from "../components/DetailPanel";
import { loadRealOutput } from "./fixtures";

describe("DetailPanel", () => {
  it("shows citation details for a selected datum", async () => {
    const user = userEvent.setup();
    const response = loadRealOutput("1b. Distribution — Lung cancer by phase");
    const row = Array.isArray(response.visualization.data) ? response.visualization.data[0] : null;
    if (!row || !Array.isArray(row.citations)) {
      throw new Error("Expected fixture row with citations");
    }

    render(
      <DetailPanel
        title={response.visualization.title}
        meta={response.meta}
        selection={{
          kind: "datum",
          title: String(row.phase ?? "Selection"),
          citations: row.citations,
          payload: row,
        }}
      />,
    );

    await user.click(screen.getByRole("tab", { name: /citations/i }));

    expect(screen.getByText(row.citations[0].nct_id)).toBeInTheDocument();
    expect(screen.getAllByText(row.citations[0].excerpt).length).toBeGreaterThan(0);
  });
});
