import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { QueryResponseSchema, type QueryResponse } from "../types/api";

const repoRoot = resolve(process.cwd(), "..");

export function loadRealOutput(name: string): QueryResponse {
  const raw = readFileSync(join(repoRoot, "real_outputs", name, "output.json"), "utf-8");
  return QueryResponseSchema.parse(JSON.parse(raw));
}

export function loadExample(name: string): QueryResponse {
  const raw = readFileSync(join(repoRoot, "examples", name), "utf-8");
  return QueryResponseSchema.parse(JSON.parse(raw));
}
