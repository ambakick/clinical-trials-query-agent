import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import {
  type QueryDraft,
  type QueryRequest,
  citationModes,
  defaultQueryDraft,
  QueryRequestSchema,
  trialPhases,
  trialStatuses,
} from "../types/api";

type QueryFormProps = {
  draft: QueryDraft;
  submitting: boolean;
  onChange: (next: QueryDraft) => void;
  onSubmit: (request: QueryRequest) => Promise<void> | void;
};

type FormErrors = Partial<Record<keyof QueryDraft, string>> & { form?: string };

function humanize(value: string): string {
  if (value === "NA") {
    return "N/A";
  }
  if (value.startsWith("EARLY_")) {
    return "Early Phase 1";
  }
  if (value.startsWith("PHASE")) {
    return value.replaceAll("PHASE", "Phase ").replaceAll("_", "/").trim();
  }
  return value.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

function toMaybeString(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed === "" ? undefined : trimmed;
}

function normalizeDraft(draft: QueryDraft): QueryRequest {
  return {
    query: draft.query.trim(),
    drug_name: toMaybeString(draft.drug_name),
    condition: toMaybeString(draft.condition),
    trial_phase: draft.trial_phase.length ? draft.trial_phase : undefined,
    sponsor: toMaybeString(draft.sponsor),
    country: toMaybeString(draft.country),
    start_year: draft.start_year.trim() === "" ? undefined : Number(draft.start_year),
    end_year: draft.end_year.trim() === "" ? undefined : Number(draft.end_year),
    status: draft.status.length ? draft.status : undefined,
    citation_mode: draft.citation_mode,
    max_results: draft.max_results.trim() === "" ? Number(defaultQueryDraft.max_results) : Number(draft.max_results),
  };
}

export function QueryForm({ draft, submitting, onChange, onSubmit }: QueryFormProps) {
  const [errors, setErrors] = useState<FormErrors>({});

  const handleFieldChange =
    (field: keyof QueryDraft) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const nextErrors = { ...errors };
      delete nextErrors[field];
      delete nextErrors.form;
      setErrors(nextErrors);
      onChange({
        ...draft,
        [field]: event.target.value as QueryDraft[keyof QueryDraft],
      });
    };

  const handleMultiSelect =
    (field: "trial_phase" | "status") => (event: ChangeEvent<HTMLSelectElement>) => {
      const values = Array.from(event.target.selectedOptions).map((option) => option.value);
      const nextErrors = { ...errors };
      delete nextErrors[field];
      delete nextErrors.form;
      setErrors(nextErrors);
      onChange({
        ...draft,
        [field]: values as QueryDraft[typeof field],
      });
    };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const payload = normalizeDraft(draft);
    const validation = QueryRequestSchema.safeParse(payload);
    if (!validation.success) {
      const nextErrors: FormErrors = {};
      for (const issue of validation.error.issues) {
        const field = issue.path[0] as keyof QueryDraft | undefined;
        if (field) {
          nextErrors[field] = issue.message;
        } else {
          nextErrors.form = issue.message;
        }
      }
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    await onSubmit(validation.data);
  };

  return (
    <form className="query-form" onSubmit={handleSubmit} noValidate>
      <div className="query-form__header">
        <div>
          <p className="eyebrow">Analyst Console</p>
          <h1>ClinicalTrials.gov Query-to-Visualization</h1>
        </div>
        <button className="query-form__submit" type="submit" disabled={submitting}>
          {submitting ? "Running…" : "Run Query"}
        </button>
      </div>

      <label className="field">
        <span>Question</span>
        <textarea
          name="query"
          value={draft.query}
          onChange={handleFieldChange("query")}
          placeholder="How has the number of pembrolizumab trials changed since 2015?"
          rows={4}
          aria-invalid={Boolean(errors.query)}
        />
        {errors.query ? <span className="field__error">{errors.query}</span> : null}
      </label>

      <details className="query-form__advanced">
        <summary>More filters</summary>
        <div className="query-form__grid">
          <label className="field">
            <span>Drug</span>
            <input value={draft.drug_name} onChange={handleFieldChange("drug_name")} placeholder="Pembrolizumab" />
          </label>
          <label className="field">
            <span>Condition</span>
            <input value={draft.condition} onChange={handleFieldChange("condition")} placeholder="Lung cancer" />
          </label>
          <label className="field">
            <span>Sponsor</span>
            <input value={draft.sponsor} onChange={handleFieldChange("sponsor")} placeholder="Merck" />
          </label>
          <label className="field">
            <span>Country</span>
            <input value={draft.country} onChange={handleFieldChange("country")} placeholder="United States" />
          </label>
          <label className="field">
            <span>Start year</span>
            <input value={draft.start_year} onChange={handleFieldChange("start_year")} inputMode="numeric" placeholder="2015" />
          </label>
          <label className="field">
            <span>End year</span>
            <input value={draft.end_year} onChange={handleFieldChange("end_year")} inputMode="numeric" placeholder="2026" />
            {errors.end_year ? <span className="field__error">{errors.end_year}</span> : null}
          </label>
          <label className="field">
            <span>Trial phase</span>
            <select multiple value={draft.trial_phase} onChange={handleMultiSelect("trial_phase")} size={6}>
              {trialPhases.map((phase) => (
                <option key={phase} value={phase}>
                  {humanize(phase)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Status</span>
            <select multiple value={draft.status} onChange={handleMultiSelect("status")} size={6}>
              {trialStatuses.map((status) => (
                <option key={status} value={status}>
                  {humanize(status)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Citation mode</span>
            <select value={draft.citation_mode} onChange={handleFieldChange("citation_mode")}>
              {citationModes.map((mode) => (
                <option key={mode} value={mode}>
                  {mode}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Max results</span>
            <input value={draft.max_results} onChange={handleFieldChange("max_results")} inputMode="numeric" placeholder="3000" />
          </label>
        </div>
      </details>

      {errors.form ? <div className="query-form__error">{errors.form}</div> : null}
    </form>
  );
}
