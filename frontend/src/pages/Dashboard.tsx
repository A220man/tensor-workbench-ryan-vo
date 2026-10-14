/** Main Dashboard page - lists SwiftPM projects with build status. */
import React, { useEffect, useState, useCallback } from "react";
import { RefreshCw, ExternalLink, Hammer, Package, ChevronDown, ChevronUp } from "lucide-react";
import { api, type Project, type ProjectStatus, type BuildStatus } from "../api";
import { Button, Badge, LoadingSpinner, EmptyState } from "../components/ui";

const statusConfig: Record<ProjectStatus, { label: string; variant: "success" | "warning" | "error" | "info" | "neutral" }> = {
  unknown: { label: "Unknown", variant: "neutral" },
  valid: { label: "Valid", variant: "success" },
  invalid: { label: "Invalid", variant: "error" },
  building: { label: "Building", variant: "warning" },
  build_failed: { label: "Build Failed", variant: "error" },
  build_success: { label: "Build Success", variant: "success" },
};

const buildStatusConfig: Record<BuildStatus, { label: string; variant: "success" | "warning" | "error" | "info" | "neutral" }> = {
  pending: { label: "Pending", variant: "neutral" },
  running: { label: "Running", variant: "warning" },
  success: { label: "Success", variant: "success" },
  failed: { label: "Failed", variant: "error" },
  cancelled: { label: "Cancelled", variant: "neutral" },
};

export const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize] = useState(20);
  const [sortConfig, setSortConfig] = useState<{ key: keyof Project; direction: "asc" | "desc" }>({
    key: "updated_at",
    direction: "desc",
  });

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listProjects({
        limit: pageSize,
        offset: page * pageSize,
      });
      setProjects(response.projects);
      setTotal(response.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load projects";
      setError(message);
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleScan = async () => {
    try {
      await api.scanWorkspace();
      await fetchProjects();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Scan failed";
      setError(message);
    }
  };

  const handleSort = (key: keyof Project) => {
    setSortConfig((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  };

  const sortedProjects = [...projects].sort((a, b) => {
    const aVal = a[sortConfig.key];
    const bVal = b[sortConfig.key];
    // Handle undefined values
    if (aVal === undefined && bVal === undefined) return 0;
    if (aVal === undefined) return sortConfig.direction === "asc" ? 1 : -1;
    if (bVal === undefined) return sortConfig.direction === "asc" ? -1 : 1;
    if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
    return 0;
  });

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="container p-6">
      {/* Header */}
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-muted text-sm mt-1">SwiftPM projects discovered in workspace</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={fetchProjects} disabled={loading} className="gap-2">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={handleScan} disabled={loading} className="gap-2">
            <Hammer size={14} />
            Scan Workspace
          </Button>
        </div>
      </header>

      {/* Error state */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm flex justify-between items-center">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchProjects}>
            Dismiss
          </Button>
        </div>
      )}

      {/* Projects Table */}
      <div className="card">
        {loading && projects.length === 0 ? (
          <div className="flex justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No projects found"
            description="Click 'Scan Workspace' to discover SwiftPM projects in your workspace directory."
            icon="folder"
            action={{ label: "Scan Workspace", onClick: handleScan }}
          />
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th onClick={() => handleSort("name")} className="cursor-pointer select-none flex items-center gap-1">
                      Project
                      {sortConfig.key === "name" && (sortConfig.direction === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                    </th>
                    <th onClick={() => handleSort("status")} className="cursor-pointer select-none flex items-center gap-1">
                      Status
                      {sortConfig.key === "status" && (sortConfig.direction === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                    </th>
                    <th>Path</th>
                    <th>Swift Tools</th>
                    <th>Targets</th>
                    <th onClick={() => handleSort("updated_at")} className="cursor-pointer select-none flex items-center gap-1">
                      Updated
                      {sortConfig.key === "updated_at" && (sortConfig.direction === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                    </th>
                    <th className="w-32">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedProjects.map((project) => (
                    <tr key={project.id}>
                      <td>
                        <div className="flex items-center gap-3">
                          <Package className="text-primary" size={18} />
                          <div>
                            <div className="font-medium">{project.name}</div>
                            {project.package_name && project.package_name !== project.name && (
                              <div className="text-sm text-muted">{project.package_name}</div>
                            )}
                            {project.package_version && (
                              <div className="text-xs text-muted">{project.package_version}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <Badge variant={statusConfig[project.status].variant}>
                          {statusConfig[project.status].label}
                        </Badge>
                      </td>
                      <td className="font-mono text-sm text-muted truncate max-w-xs" title={project.path}>
                        {project.path}
                      </td>
                      <td className="font-mono text-sm">
                        {project.swift_tools_version || "—"}
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {project.targets.length > 0 ? (
                            project.targets.slice(0, 3).map((target) => (
                              <Badge key={target} variant="neutral" className="text-xs">
                                {target}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-muted text-xs">—</span>
                          )}
                          {project.targets.length > 3 && (
                            <Badge variant="neutral" className="text-xs">
                              +{project.targets.length - 3}
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="text-sm text-muted">
                        {new Date(project.updated_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" title="Open folder">
                            <ExternalLink size={14} />
                          </Button>
                          {project.latest_build && (
                            <Badge
                              variant={buildStatusConfig[project.latest_build.status as BuildStatus].variant}
                              className="text-xs"
                            >
                              {buildStatusConfig[project.latest_build.status as BuildStatus].label}
                            </Badge>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-border-light">
                <div className="text-sm text-muted">
                  Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};