import { useState } from "react";
import type { ResponseMetadata, SelectionState } from "../types/api";

type DetailPanelProps = {
  title: string;
  meta: ResponseMetadata;
  selection: SelectionState | null;
};

type Tab = "summary" | "warnings" | "citations";

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function DetailPanel({ title, meta, selection }: DetailPanelProps) {
  const [tab, setTab] = useState<Tab>("summary");

  return (
    <aside className="detail-panel">
      <div className="detail-panel__header">
        <div>
          <p className="eyebrow">Inspection</p>
          <h2>{selection?.title ?? title}</h2>
          {selection?.subtitle ? <p className="detail-panel__subtitle">{selection.subtitle}</p> : null}
        </div>
      </div>

      <div className="detail-panel__tabs" role="tablist" aria-label="Result details">
        {(["summary", "warnings", "citations"] as Tab[]).map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={tab === name}
            className={tab === name ? "detail-panel__tab is-active" : "detail-panel__tab"}
            onClick={() => setTab(name)}
          >
            {name}
          </button>
        ))}
      </div>

      {tab === "summary" ? (
        <dl className="detail-panel__list">
          <div>
            <dt>Interpretation</dt>
            <dd>{meta.query_interpretation}</dd>
          </div>
          <div>
            <dt>Filters</dt>
            <dd>{renderValue(meta.filters_applied)}</dd>
          </div>
          <div>
            <dt>Match mode</dt>
            <dd>{meta.match_mode}</dd>
          </div>
          <div>
            <dt>Studies analyzed</dt>
            <dd>{meta.studies_analyzed}</dd>
          </div>
          <div>
            <dt>Total matched</dt>
            <dd>{renderValue(meta.total_studies_matched)}</dd>
          </div>
          <div>
            <dt>API version</dt>
            <dd>{meta.api_version}</dd>
          </div>
          <div>
            <dt>Data timestamp</dt>
            <dd>{meta.data_timestamp}</dd>
          </div>
          <div>
            <dt>Processing time</dt>
            <dd>{renderValue(meta.processing_time_ms ? `${meta.processing_time_ms} ms` : null)}</dd>
          </div>
        </dl>
      ) : null}

      {tab === "warnings" ? (
        meta.warnings.length ? (
          <ul className="detail-panel__warnings">
            {meta.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : (
          <p className="detail-panel__empty">No warnings for this result.</p>
        )
      ) : null}

      {tab === "citations" ? (
        selection?.citations?.length ? (
          <ul className="detail-panel__citations">
            {selection.citations.map((citation) => (
              <li key={`${citation.nct_id}-${citation.excerpt}`}>
                <div className="detail-panel__citation-head">
                  <strong>{citation.nct_id}</strong>
                  {citation.title ? <span>{citation.title}</span> : null}
                </div>
                <p>{citation.excerpt}</p>
                {citation.field_path ? <code>{citation.field_path}</code> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="detail-panel__empty">Select a data point to inspect source records.</p>
        )
      ) : null}
    </aside>
  );
}
