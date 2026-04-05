import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { QueryForm } from "../components/QueryForm";
import { defaultQueryDraft, type QueryDraft, type QueryRequest } from "../types/api";

function ControlledForm({
  onSubmit,
  initialDraft = defaultQueryDraft,
}: {
  onSubmit: (request: QueryRequest) => Promise<void> | void;
  initialDraft?: QueryDraft;
}) {
  const [draft, setDraft] = useState(initialDraft);
  return <QueryForm draft={draft} submitting={false} onChange={setDraft} onSubmit={onSubmit} />;
}

describe("QueryForm", () => {
  it("blocks empty queries client-side", async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();
    render(<ControlledForm onSubmit={handleSubmit} />);

    await user.click(screen.getByRole("button", { name: /run query/i }));

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(await screen.findByText(/at least 5 character/i)).toBeInTheDocument();
  });

  it("blocks inverted year ranges", async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();
    render(
      <ControlledForm
        onSubmit={handleSubmit}
        initialDraft={{
          ...defaultQueryDraft,
          query: "Show pembrolizumab trials by year",
          start_year: "2026",
          end_year: "2015",
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /run query/i }));

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(await screen.findByText(/start_year must be less than or equal to end_year/i)).toBeInTheDocument();
  });
});
