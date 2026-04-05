import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VisualizationPanel } from "../components/VisualizationPanel";
import { loadExample, loadRealOutput } from "./fixtures";

describe("VisualizationPanel fixture rendering", () => {
  it.each([
    ["1a. Time Trend — Pembrolizumab since 2015", "time-series-renderer"],
    ["1b. Distribution — Lung cancer by phase", "bar-chart-renderer"],
    ["1c. Comparison — Pembrolizumab vs Nivolumab", "grouped-bar-chart-renderer"],
    ["1e. Network — Sponsor-drug for breast cancer", "network-graph-renderer"],
  ])("renders %s without crashing", (fixture, testId) => {
    const response = loadRealOutput(fixture);
    render(<VisualizationPanel response={response} onSelect={() => undefined} />);
    expect(screen.getByText(response.visualization.title)).toBeInTheDocument();
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it("renders the scatter example fixture", () => {
    const response = loadExample("07_scatter.json");
    render(<VisualizationPanel response={response} onSelect={() => undefined} />);
    expect(screen.getByText("Enrollment vs Duration")).toBeInTheDocument();
    expect(screen.getByTestId("scatter-plot-renderer")).toBeInTheDocument();
  });
});
