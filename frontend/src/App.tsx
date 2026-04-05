import { useEffect, useMemo, useState } from "react";
import { DetailPanel } from "./components/DetailPanel";
import { QueryForm } from "./components/QueryForm";
import { VisualizationPanel } from "./components/VisualizationPanel";
import { getHealth, submitQuery } from "./lib/api";
import {
  type ClarificationResponse,
  type HealthResponse,
  type QueryDraft,
  type QueryRequest,
  type QueryResponse,
  type SelectionState,
  defaultQueryDraft,
} from "./types/api";

type LoadState = "idle" | "loading" | "success" | "clarification" | "error";

function isSuccess(response: QueryResponse | ClarificationResponse | null): response is QueryResponse {
  return Boolean(response && "visualization" in response);
}

export default function App() {
  const [draft, setDraft] = useState<QueryDraft>(defaultQueryDraft);
  const [state, setState] = useState<LoadState>("idle");
  const [response, setResponse] = useState<QueryResponse | ClarificationResponse | null>(null);
  const [lastSuccessfulRequest, setLastSuccessfulRequest] = useState<QueryRequest | null>(null);
  const [lastSuccessfulResponse, setLastSuccessfulResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    void getHealth()
      .then(setHealth)
      .catch(() => {
        setHealth(null);
      });
  }, []);

  const activeQueryResponse = useMemo(() => {
    if (isSuccess(response)) {
      return response;
    }
    if (response && "status" in response) {
      return null;
    }
    return lastSuccessfulResponse;
  }, [lastSuccessfulResponse, response]);

  const handleSubmit = async (request: QueryRequest) => {
    setState("loading");
    setError(null);
    setSelection(null);
    try {
      const nextResponse = await submitQuery(request);
      if ("status" in nextResponse) {
        setResponse(nextResponse);
        setState("clarification");
        return;
      }
      setResponse(nextResponse);
      setLastSuccessfulRequest(request);
      setLastSuccessfulResponse(nextResponse);
      setState("success");
    } catch (submissionError) {
      setState("error");
      setError(submissionError instanceof Error ? submissionError.message : "Request failed");
    }
  };

  return (
    <div className="app-shell">
      <div className="app-shell__backdrop" />
      <main className="app-shell__content">
        <header className="topbar">
          <div className="topbar__status">
            <span className={health?.ctgov.reachable ? "status-pill is-live" : "status-pill is-offline"}>
              {health?.ctgov.reachable ? "Backend Live" : "Backend Unknown"}
            </span>
            {health?.ctgov.api_version ? <span className="status-meta">CT.gov {health.ctgov.api_version}</span> : null}
          </div>
          {lastSuccessfulRequest?.query ? <p className="topbar__memory">Last successful query: {lastSuccessfulRequest.query}</p> : null}
        </header>

        <QueryForm draft={draft} submitting={state === "loading"} onChange={setDraft} onSubmit={handleSubmit} />

        {error ? <div className="banner banner--error">{error}</div> : null}
        {state === "loading" ? <div className="banner banner--loading">Submitting query to the backend…</div> : null}

        {response && "status" in response ? (
          <section className="clarification-card">
            <p className="eyebrow">Clarification Needed</p>
            <h2>{response.question}</h2>
            <p>{response.reason}</p>
            {response.suggested_interpretation ? <p className="clarification-card__suggestion">{response.suggested_interpretation}</p> : null}
          </section>
        ) : null}

        {activeQueryResponse ? (
          <section className="results-grid">
            <VisualizationPanel response={activeQueryResponse} onSelect={setSelection} />
            <DetailPanel title={activeQueryResponse.visualization.title} meta={activeQueryResponse.meta} selection={selection} />
          </section>
        ) : (
          <section className="welcome-card">
            <p className="eyebrow">Start Here</p>
            <h2>Ask a clinical-trials question and inspect the backend-generated chart.</h2>
            <p>
              The UI sends the request directly to the FastAPI backend, renders the returned visualization spec, and lets you inspect warnings
              and citations without touching the raw JSON.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
