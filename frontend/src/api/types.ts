/** API type definitions matching backend schemas. */

export type ProjectStatus = "unknown" | "valid" | "invalid" | "building" | "build_failed" | "build_success";

export type BuildStatus = "pending" | "running" | "success" | "failed" | "cancelled";

export type BuildTarget = "device" | "simulator" | "macos";

export interface ProjectTarget {
  name: string;
  type: string;
}

export interface ProjectDependency {
  url: string;
  version?: string;
}

export interface BuildSummary {
  id: number;
  target: BuildTarget;
  configuration: string;
  status: BuildStatus;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

export interface Project {
  id: number;
  name: string;
  path: string;
  package_name?: string;
  package_version?: string;
  swift_tools_version?: string;
  status: ProjectStatus;
  description?: string;
  targets: string[];
  dependencies: string[];
  latest_build?: BuildSummary;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  limit: number;
  offset: number;
}

export interface ScanResponse {
  scanned: number;
  added: number;
  updated: number;
  errors: string[];
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  version: string;
  environment: string;
  database: "ok" | "error";
}

export interface VersionResponse {
  name: string;
  version: string;
  environment: string;
  build_date?: string;
  git_commit?: string;
}