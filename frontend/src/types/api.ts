import { z } from "zod";

export const chartTypes = [
  "bar_chart",
  "grouped_bar_chart",
  "time_series",
  "network_graph",
  "pie_chart",
  "scatter_plot",
] as const;

export const citationModes = ["none", "sample", "deep"] as const;
export const matchModes = ["broad", "exact"] as const;
export const trialPhases = [
  "EARLY_PHASE1",
  "PHASE1",
  "PHASE1_PHASE2",
  "PHASE2",
  "PHASE2_PHASE3",
  "PHASE3",
  "PHASE4",
  "NA",
] as const;
export const trialStatuses = [
  "NOT_YET_RECRUITING",
  "RECRUITING",
  "ENROLLING_BY_INVITATION",
  "ACTIVE_NOT_RECRUITING",
  "COMPLETED",
  "SUSPENDED",
  "TERMINATED",
  "WITHDRAWN",
  "UNKNOWN_STATUS",
] as const;

export type ChartType = (typeof chartTypes)[number];
export type CitationMode = (typeof citationModes)[number];
export type TrialPhase = (typeof trialPhases)[number];
export type TrialStatus = (typeof trialStatuses)[number];

export const QueryRequestSchema = z
  .object({
    query: z.string().min(5).max(1000),
    drug_name: z.string().trim().min(1).optional(),
    condition: z.string().trim().min(1).optional(),
    trial_phase: z.array(z.enum(trialPhases)).optional(),
    sponsor: z.string().trim().min(1).optional(),
    country: z.string().trim().min(1).optional(),
    start_year: z.number().int().min(1990).max(2035).optional(),
    end_year: z.number().int().min(1990).max(2035).optional(),
    status: z.array(z.enum(trialStatuses)).optional(),
    citation_mode: z.enum(citationModes).default("deep"),
    max_results: z.number().int().min(1).max(10000).default(3000),
  })
  .refine(
    (value) =>
      value.start_year === undefined ||
      value.end_year === undefined ||
      value.start_year <= value.end_year,
    {
      message: "start_year must be less than or equal to end_year",
      path: ["end_year"],
    },
  );

export const CitationSchema = z.object({
  nct_id: z.string(),
  title: z.string().nullable().optional(),
  field_path: z.string().nullable().optional(),
  field_value: z.union([z.string(), z.number(), z.boolean(), z.null()]).optional(),
  excerpt: z.string(),
});

export const FieldEncodingSchema = z.object({
  field: z.string(),
  type: z.enum(["quantitative", "nominal", "ordinal", "temporal"]),
  title: z.string().nullable().optional(),
  sort: z.string().nullable().optional(),
  format: z.string().nullable().optional(),
});

export const NetworkNodeSchema = z.object({
  id: z.string(),
  label: z.string(),
  type: z.string(),
  size: z.number(),
  metadata: z.record(z.any()).nullable().optional(),
});

export const NetworkEdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  weight: z.number(),
  citations: z.array(CitationSchema).nullable().optional(),
});

export const NetworkDataSchema = z.object({
  nodes: z.array(NetworkNodeSchema),
  edges: z.array(NetworkEdgeSchema),
});

export const VisualizationSpecSchema = z.object({
  type: z.enum(chartTypes),
  title: z.string(),
  description: z.string().nullable().optional(),
  encoding: z.record(FieldEncodingSchema),
  data: z.union([z.array(z.record(z.any())), NetworkDataSchema]),
  render_hints: z.record(z.any()).nullable().optional(),
});

export const ResponseMetadataSchema = z.object({
  query_interpretation: z.string(),
  filters_applied: z.record(z.any()),
  match_mode: z.enum(matchModes),
  total_studies_matched: z.number().int().nullable().optional(),
  studies_analyzed: z.number().int(),
  data_source: z.string(),
  api_version: z.string(),
  data_timestamp: z.string(),
  warnings: z.array(z.string()),
  processing_time_ms: z.number().int().nullable().optional(),
});

export const QueryResponseSchema = z.object({
  visualization: VisualizationSpecSchema,
  meta: ResponseMetadataSchema,
});

export const ClarificationResponseSchema = z.object({
  status: z.literal("needs_clarification"),
  reason: z.string(),
  question: z.string(),
  suggested_interpretation: z.string().nullable().optional(),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;
export type Citation = z.infer<typeof CitationSchema>;
export type FieldEncoding = z.infer<typeof FieldEncodingSchema>;
export type NetworkNode = z.infer<typeof NetworkNodeSchema>;
export type NetworkEdge = z.infer<typeof NetworkEdgeSchema>;
export type NetworkData = z.infer<typeof NetworkDataSchema>;
export type VisualizationSpec = z.infer<typeof VisualizationSpecSchema>;
export type ResponseMetadata = z.infer<typeof ResponseMetadataSchema>;
export type QueryResponse = z.infer<typeof QueryResponseSchema>;
export type ClarificationResponse = z.infer<typeof ClarificationResponseSchema>;
export type ApiResponse = QueryResponse | ClarificationResponse;

export type QueryDraft = {
  query: string;
  drug_name: string;
  condition: string;
  trial_phase: TrialPhase[];
  sponsor: string;
  country: string;
  start_year: string;
  end_year: string;
  status: TrialStatus[];
  citation_mode: CitationMode;
  max_results: string;
};

export const defaultQueryDraft: QueryDraft = {
  query: "",
  drug_name: "",
  condition: "",
  trial_phase: [],
  sponsor: "",
  country: "",
  start_year: "",
  end_year: "",
  status: [],
  citation_mode: "deep",
  max_results: "3000",
};

export const HealthResponseSchema = z.object({
  status: z.string(),
  planner_provider: z.string(),
  planner_configured: z.boolean(),
  ctgov: z.object({
    reachable: z.boolean(),
    api_version: z.string().optional(),
    data_timestamp: z.string().optional(),
  }),
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;

export type SelectionState = {
  kind: "datum" | "node" | "edge";
  title: string;
  subtitle?: string;
  citations: Citation[];
  payload: Record<string, unknown>;
};
