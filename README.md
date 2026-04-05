# ClinicalTrials.gov Query-to-Visualization Backend

Backend service that converts natural-language clinical trial questions into structured visualization responses backed by ClinicalTrials.gov.

## Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- httpx
- OpenAI API (`gpt-4.1`) for planning only
- Plain Python collections for aggregation

## Run

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2. Configure environment:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` or in your shell.

3. Start the server:

```bash
uvicorn app.main:app --reload
```

## API

### `POST /api/v1/query`

Required:

- `query: string`

Optional:

- `drug_name`
- `condition`
- `trial_phase`
- `sponsor`
- `country`
- `start_year`
- `end_year`
- `status`
- `citation_mode`
- `max_results`

Example:

```json
{
  "query": "How are lung cancer trials distributed across phases?",
  "condition": "Lung cancer"
}
```

### Success response

Returns:

- `visualization`
  - `type`
  - `title`
  - `encoding`
  - `data`
- `meta`
  - `query_interpretation`
  - `filters_applied`
  - `match_mode`
  - `total_studies_matched`
  - `studies_analyzed`
  - `api_version`
  - `data_timestamp`
  - `warnings`

### Clarification response

When the request is materially ambiguous, the service returns:

```json
{
  "status": "needs_clarification",
  "reason": "Ambiguous comparison target",
  "question": "Which two drugs should be compared?"
}
```

## Supported query classes

- time trend
- distribution
- comparison
- geographic
- relationship network
- ranking
- scatter

## Supported chart types

- `bar_chart`
- `grouped_bar_chart`
- `time_series`
- `network_graph`
- `pie_chart`
- `scatter_plot`

`pie_chart` is only used for low-cardinality composition queries.

`scatter_plot` is used for study-level metric comparisons such as enrollment versus duration.

## Design decisions

- The LLM produces only `AnalysisPlan`, never API params or data rows.
- The compiler owns CT.gov search semantics.
- CT.gov calls are cached and rate-limited.
- Aggregation uses plain Python collections instead of Polars because the dataset size is small and reviewer readability matters more.
- Citations are attached during aggregation.

## Caching

- `L1`: `AnalysisPlan`
- `L3`: raw CT.gov responses
- `L5`: final query response

`dataTimestamp` invalidates `L3` and `L5`.

## Testing

```bash
pytest
```

## Limitations

- Requires an OpenAI API key for live planning
- Uses a custom visualization DSL instead of a full chart grammar
- Exact vs broad semantics are implemented for supported cases only
- Some advanced CT.gov filters are intentionally not exposed in v1

## Validation and tools used

- Used AI-assisted drafting while validating architecture and API behavior against the live ClinicalTrials.gov API
- Validated correctness with model tests, compiler tests, processor tests, cache tests, API tests, and syntax compilation
- The deterministic compiler, normalizer, processors, and cache strategy were implemented deliberately around the design
