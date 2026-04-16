# ClinicalTrials.gov Query-to-Visualization Backend

Backend service that converts natural-language clinical trial questions into structured visualization responses backed by ClinicalTrials.gov.

## Demo video: [https://youtu.be/YLnxIQ7P8ck](https://youtu.be/YLnxIQ7P8ck)

Real example outputs produced by the backend are available in `real_outputs` folder in the repo

## Architecture

```
                            POST /api/v1/query
                                    |
                                    v
                          +-------------------+
                          |  Request Validation|
                          |  (Pydantic v2)     |
                          +---------+---------+
                                    |
                          +---------v---------+
                          |   LLM Planner     |     "LLM reasons,
                          |   (gpt-4.1)       |      compiler constrains,
                          |                   |      code executes."
                          |  Emits semantic   |
                          |  AnalysisPlan     |
                          +---------+---------+
                                    |
                     +--------------v--------------+
                     |    Deterministic Compiler    |
                     |                              |
                     |  AnalysisPlan -> FetchPlan   |
                     |  - owns CT.gov API semantics |
                     |  - broad vs exact search     |
                     |  - field projection          |
                     |  - filter.advanced clauses   |
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |    CT.gov Client             |
                     |                              |
                     |  - async HTTP (httpx)        |
                     |  - pagination                |
                     |  - rate limiter (40 req/min) |
                     |  - retry w/ backoff          |
                     |  - L3 response cache         |
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |  Canonical Normalization     |
                     |                              |
                     |  Raw JSON -> StudyRecord,    |
                     |  ConditionFact, SponsorFact, |
                     |  InterventionFact,           |
                     |  LocationFact, ProvenanceFact|
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |   Processor Registry         |
                     |                              |
                     |  time_trend   -> TimeTrend   |
                     |  distribution -> Distribution|
                     |  comparison   -> Comparison  |
                     |  geographic   -> Geographic  |
                     |  network      -> Network     |
                     |  ranking      -> Ranking     |
                     |  scatter      -> Scatter     |
                     +--------------+--------------+
                                    |
                     +--------------v--------------+
                     |  Visualization Builder       |
                     |  + Citation Engine           |
                     |                              |
                     |  -> VisualizationSpec        |
                     |  -> ResponseMetadata         |
                     +--------------+--------------+
                                    |
                                    v
                            QueryResponse JSON


Cache layers:
  L1  AnalysisPlan          (30 min TTL, keyed by request + prompt version)
  L3  Raw CT.gov responses  (1 hr TTL, keyed by params + dataTimestamp)
  L5  Final QueryResponse   (15 min TTL, keyed by request + dataTimestamp)
```

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

## Frontend

A live React/Vite frontend now lives in frontend

Run it in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

By default:
- FastAPI runs on `http://localhost:8000`
- Vite runs on `http://localhost:5173`

The backend allows `http://localhost:5173` via CORS by default. Override with `CORS_ALLOW_ORIGINS` if needed.

To build or test the frontend:

```bash
cd frontend
npm test
npm run build
```

## Design decisions

### 1. The LLM produces only `AnalysisPlan`, never API params or data rows

The most important design choice in this system is the boundary around the model. The LLM is used only for **semantic planning**, not for factual execution.

Concretely, the planner is allowed to decide:

- what query class the user is asking for
- what entities are present in the question
- what filters are implied
- what grouping/measure/chart family is appropriate
- whether the request is broad enough to need clarification

The planner is explicitly **not** allowed to decide:

- raw ClinicalTrials.gov request parameters
- which CT.gov field names to fetch
- which records count toward the answer
- any chart values, counts, nodes, edges, or citations

That separation is deliberate for two reasons:

- it reduces hallucination risk by preventing the model from fabricating facts or inventing unsupported API syntax
- it keeps the LLM output stable even if the CT.gov query strategy changes later

In practice, this means the model returns a typed `AnalysisPlan`, and all factual work happens afterward in deterministic code. This is the core anti-hallucination constraint in the system.

### 2. The compiler owns CT.gov search semantics

The compiler is the hard boundary between user intent and upstream API execution. It translates `AnalysisPlan` into `FetchPlan` and owns all ClinicalTrials.gov-specific logic.

That includes:

- choosing `broad` vs `exact` match mode
- selecting between CT.gov query-area parameters and `filter.advanced`
- deciding which fields must be projected for normalization and filtering
- combining advanced clauses correctly when multiple constraints are present
- applying safe defaults for pagination and truncation

This is important because CT.gov semantics are subtle. For example:

- some filters are only supported through `filter.advanced`
- some field shorthands are valid while others are not
- broad query-area search and exact field-scoped search do not produce identical cohorts

By centralizing those decisions in the compiler, the system gets:

- consistent execution across similar queries
- easier testing of compiled API behavior
- the ability to evolve CT.gov strategy without rewriting prompts

This also made it practical to validate API behavior against the live CT.gov service and then encode those findings in one place.

### 3. CT.gov calls are cached and rate-limited

The upstream data source is a public API, so the service is designed to be respectful of rate limits and to avoid repeating unnecessary work.

The backend uses three cache layers:

- `L1` planner cache for validated `AnalysisPlan`
- `L3` raw CT.gov response cache
- `L5` final response cache for complete `QueryResponse`

The invalidation strategy is tied to CT.gov freshness:

- CT.gov `dataTimestamp` is incorporated into raw-response and final-response cache keys
- when CT.gov publishes new data, those cache keys naturally roll over
- planner cache does not depend on `dataTimestamp`, because user intent does not become stale when the source data refreshes

The client also includes proactive rate limiting and retry behavior:

- a process-level throttle keeps traffic below the observed CT.gov threshold
- retries are used for transient `429` and `5xx` failures
- version metadata is refreshed on a bounded interval and reused between requests

This combination matters more than raw speed. It prevents retry storms, avoids avoidable upstream load, and keeps repeated interactive queries fast without sacrificing correctness.

### 4. Aggregation uses plain Python collections instead of Polars

The aggregation layer intentionally uses plain Python data structures such as:

- `Counter`
- `defaultdict(set)`
- simple loops and explicit grouping helpers

This was a deliberate tradeoff.

At this project’s scale, the service is aggregating a few thousand normalized studies per request, not millions of rows. For that workload, plain Python is more than sufficient and has several advantages:

- it keeps the code easy to read for reviewers
- it avoids a heavy dataframe dependency for relatively simple group-by/count logic
- it reduces Docker image size and dependency complexity
- it makes the aggregation rules explicit instead of hiding behavior in dataframe pipelines

Using plain Python also makes correctness easier to inspect. For example, rules like:

- count distinct `nct_id`
- prune network nodes before recomputing edges
- attach citation samples per bucket

are all visible directly in the processor code instead of being embedded in chained dataframe transforms.

If the service later grows into much larger cached/materialized datasets, a dataframe engine could be reconsidered. For the current workload and assignment goals, plain Python is the more sensible engineering choice.

### 5. Citations are attached during aggregation

Source traceability is treated as a first-class requirement, not a post-processing feature.

The backend captures provenance during normalization and carries it into aggregation so that each returned datum can include supporting citations. This means:

- bars carry citations from studies that contributed to that category
- comparison buckets carry citations from the underlying cohort/category combination
- scatter points carry study-level citations
- network edges carry citations from contributing co-occurrence studies

This design is stronger than generating citations afterward because the citation path stays coupled to the actual deterministic computation. The same code that increments a bucket or edge weight is also responsible for deciding which source studies justify that value.

That gives the system:

- auditability for every returned chart element
- cleaner support for the assignment’s deep-citation bonus
- a more frontend-friendly contract, since the UI can surface citations directly from the returned payload without reconstructing provenance itself

In short, citations are part of the analytic result, not decorative metadata layered on after the fact.

## Caching

- `L1`: `AnalysisPlan`
- `L3`: raw CT.gov responses
- `L5`: final query response

`dataTimestamp` invalidates `L3` and `L5`.


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

#### Request schema

| Field | Type | Required | Default | Validation / Notes |
| --- | --- | --- | --- | --- |
| `query` | `string` | Yes | None | `min_length=5`, `max_length=1000` |
| `drug_name` | `string \| null` | No | `null` | Optional structured hint used to override planner-inferred drug/entity selection |
| `condition` | `string \| null` | No | `null` | Optional structured hint used to override planner-inferred condition selection |
| `trial_phase` | `TrialPhase[] \| null` | No | `null` | Array of `EARLY_PHASE1`, `PHASE1`, `PHASE1_PHASE2`, `PHASE2`, `PHASE2_PHASE3`, `PHASE3`, `PHASE4`, `NA` |
| `sponsor` | `string \| null` | No | `null` | Optional structured hint used to override planner-inferred sponsor selection |
| `country` | `string \| null` | No | `null` | Optional structured hint used to override planner-inferred geography |
| `start_year` | `int \| null` | No | `null` | Inclusive lower bound, `ge=1990`, `le=2035` |
| `end_year` | `int \| null` | No | `null` | Inclusive upper bound, `ge=1990`, `le=2035` |
| `status` | `TrialStatus[] \| null` | No | `null` | Array of `NOT_YET_RECRUITING`, `RECRUITING`, `ENROLLING_BY_INVITATION`, `ACTIVE_NOT_RECRUITING`, `COMPLETED`, `SUSPENDED`, `TERMINATED`, `WITHDRAWN`, `UNKNOWN_STATUS` |
| `citation_mode` | `CitationMode` | No | `deep` | Enum: `none`, `sample`, `deep` |
| `max_results` | `int` | No | `3000` | `ge=1`, `le=10000` |

Additional request validation:

| Rule | Description |
| --- | --- |
| `start_year <= end_year` | Enforced by a model-level validator when both fields are present |
| Structured hints override planner inference | `drug_name`, `condition`, `trial_phase`, `sponsor`, `country`, `start_year`, `end_year`, and `status` take precedence over inferred plan fields before compilation |

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

#### Response schema

Top-level `QueryResponse`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `visualization` | `VisualizationSpec` | Yes | Frontend-ready visualization specification |
| `meta` | `ResponseMetadata` | Yes | Execution metadata, filters, source freshness, and warnings |

`ResponseMetadata`:

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `query_interpretation` | `string` | Yes | None | Human-readable interpretation of the natural-language request |
| `filters_applied` | `dict[string, any]` | Yes | `{}` | Normalized filters that were actually used during compilation/execution |
| `match_mode` | `MatchMode` | Yes | None | `broad` or `exact` |
| `total_studies_matched` | `int \| null` | No | `null` | Total studies reported by CT.gov before local pruning/truncation |
| `studies_analyzed` | `int` | Yes | None | Number of studies that actually contributed to the returned visualization |
| `data_source` | `string` | Yes | `clinicaltrials.gov` | Upstream authoritative source |
| `api_version` | `string` | Yes | None | CT.gov API version returned by `/api/v2/version` |
| `data_timestamp` | `string` | Yes | None | CT.gov data freshness timestamp used in cache invalidation |
| `warnings` | `string[]` | Yes | `[]` | Non-fatal execution warnings such as truncation or pruning |
| `processing_time_ms` | `int \| null` | No | `null` | Optional end-to-end latency emitted by the backend |

`VisualizationSpec`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | `ChartType` | Yes | One of `bar_chart`, `grouped_bar_chart`, `time_series`, `network_graph`, `pie_chart`, `scatter_plot` |
| `title` | `string` | Yes | Human-readable chart title |
| `description` | `string \| null` | No | Optional chart description |
| `encoding` | `dict[string, FieldEncoding]` | Yes | Channel mapping from logical data fields to visual roles |
| `data` | `list[dict[string, any]] \| NetworkData` | Yes | Frontend-ready rows for charts or node/edge payload for networks |
| `render_hints` | `dict[string, any] \| null` | No | Optional renderer-specific hints |

`FieldEncoding`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `field` | `string` | Yes | Data field name used by the renderer |
| `type` | `DataType` | Yes | `quantitative`, `nominal`, `ordinal`, or `temporal` |
| `title` | `string \| null` | No | Optional axis/legend label |
| `sort` | `string \| null` | No | Optional frontend sort hint |
| `format` | `string \| null` | No | Optional frontend formatting hint |

`Citation` objects attached to chart rows or edges:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `nct_id` | `string` | Yes | Contributing study identifier |
| `title` | `string \| null` | No | Study title when available |
| `field_path` | `string \| null` | No | Source field path inside the CT.gov response |
| `field_value` | `string \| int \| float \| bool \| null` | No | Supporting raw field value |
| `excerpt` | `string` | Yes | Human-readable traceability snippet |

`NetworkData`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `nodes` | `NetworkNode[]` | Yes | Network nodes to render |
| `edges` | `NetworkEdge[]` | Yes | Weighted edges between nodes |

`NetworkNode`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` | Yes | Stable node identifier |
| `label` | `string` | Yes | Human-readable node label |
| `type` | `string` | Yes | Node category such as `drug`, `sponsor`, or `condition` |
| `size` | `int \| float` | Yes | Relative node weight/frequency |
| `metadata` | `dict[string, any] \| null` | No | Optional additional renderer metadata |

`NetworkEdge`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `source` | `string` | Yes | Source node id |
| `target` | `string` | Yes | Target node id |
| `weight` | `int \| float` | Yes | Edge weight, typically study co-occurrence count |
| `citations` | `Citation[] \| null` | No | Supporting studies for that edge |

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

### Supported visualization types

| Chart type | Used for | Data shape |
| --- | --- | --- |
| `bar_chart` | Distribution, geographic, ranking | `[{category-or-country, trial_count, citations}]` |
| `grouped_bar_chart` | Comparison | `[{category, series, trial_count, citations}]` |
| `time_series` | Time trend | `[{year, trial_count, citations}]` |
| `scatter_plot` | Enrollment vs duration and other study-level numeric comparisons | `[{nct_id, title, enrollment_count, duration_months, citations}]` |
| `network_graph` | Sponsor-drug, drug-drug, or sponsor-condition relationships | `{nodes: [{id, label, type, size}], edges: [{source, target, weight, citations}]}` |
| `pie_chart` | Low-cardinality part-to-whole distributions | Same row shape as `bar_chart` |

This custom response schema is designed so a frontend engineer can implement a renderer without guessing field names, encodings, or citation attachment points.


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

Tools used:

- Claude Code for code generation, review-driven iteration, and architecture refinement
- OpenAI `gpt-4.1` as the runtime planner model that emits `AnalysisPlan`
- `pytest` for automated backend validation
- `httpx` for live ClinicalTrials.gov API validation during implementation
- Insomnia for manual endpoint testing of `/api/v1/query`, `/api/v1/health`, and schema endpoints

How correctness was validated:

- `25` automated backend tests covering request validation, planner caching and structured-hint precedence, compiler output for each query class, combined `filter.advanced` clause generation, processor aggregation logic, network edge construction, cache hit/miss behavior, and API endpoint integration
- Additional frontend fixture/component tests validate that the renderer layer can consume real backend payloads from `real_outputs` folder without guessing schema details
- All key CT.gov API parameter choices were validated against the live API before implementation, including supported field shorthands, `filter.advanced` syntax, `filter.overallStatus` separators, pagination behavior, and version metadata handling
- The repository is validated with `pytest -q`, `frontend/npm test`, and `frontend/npm run build`
